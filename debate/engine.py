"""
Multi-Agent Debate Engine
=========================
Orchestrates structured debate across 8 expert agents over K rounds,
tracking proposals, critiques, revisions, and convergence.

Adapts the COMPASS ensemble call pattern (ensemble.py) for policy debate
rather than clinical decision-making.
"""

import json
import os
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .personas import (
    AgentPersona,
    build_personas,
    build_proposal_prompt,
    build_critique_prompt,
    build_revision_prompt,
    build_minority_report_prompt,
)
from .domains import build_domains, get_domain_descriptions
from .convergence import ConvergenceTracker
from .parser import extract_parameters, ParameterSet

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Call Infrastructure (adapted from COMPASS ensemble.py)
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """Configuration for the LLM used in debate."""
    provider: str = "anthropic"  # "anthropic", "openai", "google"
    model_id: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key_env: str = "ANTHROPIC_API_KEY"
    rate_limit_delay: float = 1.0  # seconds between calls


@dataclass
class DebateConfig:
    """Configuration for the debate process."""
    max_rounds: int = 6
    convergence_cv_threshold: float = 0.15
    convergence_domains_required: int = 10  # out of 12
    convergence_stability_rounds: int = 2  # must hold for 2 consecutive rounds
    minority_report_threshold_sd: float = 1.0
    critique_sample_size: int = 3  # each agent critiques N others (not all 7)
    output_dir: str = "output/debate"
    llm: LLMConfig = field(default_factory=LLMConfig)


@dataclass
class DebateRound:
    """Record of a single debate round."""
    round_num: int
    proposals: Dict[str, str]  # agent_id -> raw JSON proposal
    critiques: Dict[str, Dict[str, str]]  # agent_id -> {target_id: critique}
    parsed_parameters: Dict[str, ParameterSet]  # agent_id -> parsed params
    convergence_scores: Dict[str, float]  # domain_id -> CV
    converged_domains: List[str]
    timestamp: float = 0.0


class DebateEngine:
    """
    Orchestrates multi-agent debate for AI ACO design.

    Flow:
        1. Round 0: Each agent generates independent proposal
        2. Rounds 1-K: Critique → Revise → Track convergence
        3. Convergence check after each round
        4. Minority reports for dissenting agents
    """

    def __init__(self, config: Optional[DebateConfig] = None):
        self.config = config or DebateConfig()
        self.personas = build_personas()
        self.domains = build_domains()
        self.domain_descriptions = get_domain_descriptions()
        self.tracker = ConvergenceTracker(
            domain_ids=list(self.domains.keys()),
            cv_threshold=self.config.convergence_cv_threshold,
            domains_required=self.config.convergence_domains_required,
            stability_rounds=self.config.convergence_stability_rounds,
        )
        self.rounds: List[DebateRound] = []
        self._llm_client = None

        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # LLM client management
    # -------------------------------------------------------------------

    def _get_client(self):
        """Lazy-initialize LLM client."""
        if self._llm_client is not None:
            return self._llm_client

        cfg = self.config.llm
        if cfg.provider == "anthropic":
            import anthropic
            api_key = os.environ.get(cfg.api_key_env)
            self._llm_client = anthropic.Anthropic(api_key=api_key)
        elif cfg.provider == "openai":
            from openai import OpenAI
            api_key = os.environ.get(cfg.api_key_env, os.environ.get("OPENAI_API_KEY"))
            self._llm_client = OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {cfg.provider}")
        return self._llm_client

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM with rate limiting. Returns raw text response."""
        cfg = self.config.llm
        time.sleep(cfg.rate_limit_delay)

        client = self._get_client()

        try:
            if cfg.provider == "anthropic":
                response = client.messages.create(
                    model=cfg.model_id,
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    timeout=300,
                )
                return response.content[0].text.strip()

            elif cfg.provider == "openai":
                response = client.chat.completions.create(
                    model=cfg.model_id,
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=300,
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return json.dumps({"error": str(e)})

    # -------------------------------------------------------------------
    # Debate phases
    # -------------------------------------------------------------------

    def run_round_zero(self) -> DebateRound:
        """Round 0: Independent proposals from all agents."""
        logger.info("=== ROUND 0: Independent Proposals ===")
        proposals = {}
        parsed = {}

        for agent_id, persona in self.personas.items():
            logger.info(f"  Agent {agent_id} ({persona.name}) generating proposal...")
            prompt = build_proposal_prompt(persona, self.domain_descriptions)
            raw = self._call_llm(persona.system_prompt, prompt)
            proposals[agent_id] = raw
            parsed[agent_id] = extract_parameters(raw, list(self.domains.keys()))
            logger.info(f"    Parsed {len(parsed[agent_id].values)} parameter values")

        # Compute initial convergence
        cv_scores = self.tracker.compute_round_cv(parsed)
        converged = self.tracker.get_converged_domains(cv_scores)

        round_data = DebateRound(
            round_num=0,
            proposals=proposals,
            critiques={},
            parsed_parameters=parsed,
            convergence_scores=cv_scores,
            converged_domains=converged,
            timestamp=time.time(),
        )
        self.rounds.append(round_data)
        self._save_round(round_data)

        logger.info(f"  Converged domains: {len(converged)}/12 (threshold: {self.config.convergence_domains_required})")
        return round_data

    def run_debate_round(self, round_num: int) -> DebateRound:
        """Rounds 1-K: Critique and revise."""
        logger.info(f"=== ROUND {round_num}: Critique & Revise ===")
        prev = self.rounds[-1]
        agent_ids = list(self.personas.keys())

        # Phase 1: Each agent critiques a sample of others
        all_critiques: Dict[str, Dict[str, str]] = {}
        for agent_id in agent_ids:
            persona = self.personas[agent_id]
            # Select critique targets (sample N others, prioritize most-divergent)
            targets = self._select_critique_targets(agent_id, prev)
            critiques = {}
            for target_id in targets:
                logger.info(f"  {agent_id} critiquing {target_id}...")
                prompt = build_critique_prompt(
                    persona,
                    prev.proposals[target_id],
                    self.personas[target_id].name,
                    round_num,
                )
                critiques[target_id] = self._call_llm(persona.system_prompt, prompt)
            all_critiques[agent_id] = critiques

        # Phase 2: Each agent revises based on critiques received
        proposals = {}
        parsed = {}
        for agent_id in agent_ids:
            persona = self.personas[agent_id]
            # Collect critiques addressed TO this agent
            critiques_received = {}
            for critic_id, critic_targets in all_critiques.items():
                if agent_id in critic_targets:
                    critiques_received[critic_id] = critic_targets[agent_id]

            if critiques_received:
                critiques_text = "\n\n".join(
                    f"--- From {self.personas[cid].name} ({self.personas[cid].role}) ---\n{text}"
                    for cid, text in critiques_received.items()
                )
            else:
                critiques_text = "No critiques received this round."

            logger.info(f"  {agent_id} revising proposal (received {len(critiques_received)} critiques)...")
            prompt = build_revision_prompt(
                persona,
                prev.proposals[agent_id],
                critiques_text,
                round_num,
            )
            raw = self._call_llm(persona.system_prompt, prompt)
            proposals[agent_id] = raw
            parsed[agent_id] = extract_parameters(raw, list(self.domains.keys()))

        # Compute convergence
        cv_scores = self.tracker.compute_round_cv(parsed)
        converged = self.tracker.get_converged_domains(cv_scores)

        round_data = DebateRound(
            round_num=round_num,
            proposals=proposals,
            critiques=all_critiques,
            parsed_parameters=parsed,
            convergence_scores=cv_scores,
            converged_domains=converged,
            timestamp=time.time(),
        )
        self.rounds.append(round_data)
        self._save_round(round_data)

        logger.info(f"  Converged domains: {len(converged)}/12")
        return round_data

    def generate_minority_reports(self) -> Dict[str, str]:
        """Generate minority reports for agents diverging from consensus."""
        if not self.rounds:
            return {}

        final_round = self.rounds[-1]
        consensus = self.tracker.compute_consensus(final_round.parsed_parameters)
        consensus_json = json.dumps(consensus, indent=2, default=str)

        reports = {}
        for agent_id, params in final_round.parsed_parameters.items():
            divergent = self.tracker.get_divergent_parameters(
                params, consensus, threshold_sd=self.config.minority_report_threshold_sd
            )
            if divergent:
                logger.info(f"  {agent_id} diverges on {len(divergent)} parameters — generating minority report")
                persona = self.personas[agent_id]
                prompt = build_minority_report_prompt(
                    persona, consensus_json, final_round.proposals[agent_id]
                )
                reports[agent_id] = self._call_llm(persona.system_prompt, prompt)

        return reports

    # -------------------------------------------------------------------
    # Main orchestration
    # -------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Run the complete debate pipeline.

        Returns dict with:
            consensus_design: final consensus parameter values
            minority_reports: dissenting positions
            convergence_history: CV scores by round by domain
            rounds: all round data
        """
        logger.info("Starting AI ACO Multi-Agent Debate")
        logger.info(f"  Agents: {len(self.personas)}")
        logger.info(f"  Domains: {len(self.domains)}")
        logger.info(f"  Max rounds: {self.config.max_rounds}")

        # Round 0: Independent proposals
        self.run_round_zero()

        # Rounds 1-K: Debate until convergence or max rounds
        for r in range(1, self.config.max_rounds + 1):
            round_data = self.run_debate_round(r)

            if self.tracker.is_converged(round_data.convergence_scores, r):
                logger.info(f"  CONVERGED at round {r}")
                break
        else:
            logger.info(f"  Reached max rounds ({self.config.max_rounds}) without full convergence")

        # Generate consensus and minority reports
        final_round = self.rounds[-1]
        consensus = self.tracker.compute_consensus(final_round.parsed_parameters)
        minority_reports = self.generate_minority_reports()

        # Build convergence history
        convergence_history = {
            domain_id: [r.convergence_scores.get(domain_id, float("nan")) for r in self.rounds]
            for domain_id in self.domains
        }

        # Save final results
        results = {
            "consensus_design": consensus,
            "minority_reports": {k: v for k, v in minority_reports.items()},
            "convergence_history": convergence_history,
            "total_rounds": len(self.rounds),
            "converged": self.tracker.is_converged(
                final_round.convergence_scores, len(self.rounds) - 1
            ),
            "final_converged_domains": final_round.converged_domains,
        }
        self._save_results(results)

        return results

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _select_critique_targets(
        self, agent_id: str, prev_round: DebateRound
    ) -> List[str]:
        """Select which agents to critique (most divergent from self)."""
        import random

        other_ids = [aid for aid in self.personas if aid != agent_id]

        if len(other_ids) <= self.config.critique_sample_size:
            return other_ids

        # Prioritize agents with most-different parameter values
        if agent_id in prev_round.parsed_parameters:
            my_params = prev_round.parsed_parameters[agent_id]
            divergences = []
            for oid in other_ids:
                if oid in prev_round.parsed_parameters:
                    div = self.tracker.parameter_distance(
                        my_params, prev_round.parsed_parameters[oid]
                    )
                    divergences.append((oid, div))
            divergences.sort(key=lambda x: -x[1])
            return [oid for oid, _ in divergences[: self.config.critique_sample_size]]

        return random.sample(other_ids, self.config.critique_sample_size)

    def _save_round(self, round_data: DebateRound):
        """Save round data to disk."""
        outdir = Path(self.config.output_dir)
        path = outdir / f"round_{round_data.round_num}.json"
        data = {
            "round_num": round_data.round_num,
            "proposals": round_data.proposals,
            "critiques": round_data.critiques,
            "convergence_scores": round_data.convergence_scores,
            "converged_domains": round_data.converged_domains,
            "timestamp": round_data.timestamp,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"  Saved round {round_data.round_num} to {path}")

    def _save_results(self, results: Dict):
        """Save final debate results."""
        outdir = Path(self.config.output_dir)
        path = outdir / "debate_results.json"
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Saved final results to {path}")
