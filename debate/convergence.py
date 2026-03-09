"""
Convergence Tracker for Multi-Agent Debate
==========================================
Monitors parameter-level convergence across agents using coefficient of
variation (CV). Debate converges when CV < threshold for ≥K domains
over M consecutive rounds (Delphi-like stability criterion).
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .parser import ParameterSet

logger = logging.getLogger(__name__)


class ConvergenceTracker:
    """
    Tracks convergence of agent proposals across debate rounds.

    For numeric parameters: CV = std / mean across agents
    For categorical parameters: 1 - (max_agreement_fraction)
    Convergence declared when CV < threshold for ≥domains_required
    domains for stability_rounds consecutive rounds.
    """

    def __init__(
        self,
        domain_ids: List[str],
        cv_threshold: float = 0.15,
        domains_required: int = 10,
        stability_rounds: int = 2,
    ):
        self.domain_ids = domain_ids
        self.cv_threshold = cv_threshold
        self.domains_required = domains_required
        self.stability_rounds = stability_rounds
        self._history: List[Dict[str, float]] = []  # round -> {domain: cv}

    def compute_round_cv(
        self, parsed_params: Dict[str, ParameterSet]
    ) -> Dict[str, float]:
        """
        Compute coefficient of variation for each domain across all agents.

        For each domain, collects all numeric sub-parameter values across agents,
        computes per-sub-parameter CV, then averages across sub-parameters.
        For categorical sub-parameters, uses disagreement rate (1 - mode fraction).
        """
        domain_cvs = {}

        for domain_id in self.domain_ids:
            sub_param_cvs = []

            # Collect all sub-parameter keys for this domain across agents
            all_sub_keys = set()
            for agent_params in parsed_params.values():
                for key in agent_params.values:
                    if key.startswith(f"{domain_id}."):
                        sub_key = key.split(".", 1)[1]
                        all_sub_keys.add(sub_key)

            for sub_key in all_sub_keys:
                values = []
                categorical_values = []
                for agent_id, agent_params in parsed_params.items():
                    pv = agent_params.get(domain_id, sub_key)
                    if pv is None:
                        continue
                    # Try numeric
                    try:
                        values.append(float(pv.value))
                    except (TypeError, ValueError):
                        categorical_values.append(str(pv.value))

                if len(values) >= 2:
                    mean_val = np.mean(values)
                    if mean_val != 0:
                        cv = np.std(values) / abs(mean_val)
                    else:
                        cv = 0.0 if np.std(values) == 0 else 1.0
                    sub_param_cvs.append(cv)
                elif len(categorical_values) >= 2:
                    # Disagreement rate for categorical
                    from collections import Counter
                    counts = Counter(categorical_values)
                    mode_frac = counts.most_common(1)[0][1] / len(categorical_values)
                    sub_param_cvs.append(1.0 - mode_frac)

            if sub_param_cvs:
                domain_cvs[domain_id] = float(np.mean(sub_param_cvs))
            else:
                domain_cvs[domain_id] = 1.0  # no data = maximum disagreement

        self._history.append(domain_cvs)
        return domain_cvs

    def get_converged_domains(self, cv_scores: Dict[str, float]) -> List[str]:
        """Return domain IDs with CV below threshold."""
        return [d for d, cv in cv_scores.items() if cv < self.cv_threshold]

    def is_converged(self, cv_scores: Dict[str, float], round_num: int) -> bool:
        """
        Check if debate has converged (Delphi stability criterion).

        Requires ≥domains_required domains below CV threshold
        for stability_rounds consecutive rounds.
        """
        n_converged = len(self.get_converged_domains(cv_scores))
        if n_converged < self.domains_required:
            return False

        # Check stability over recent rounds
        if len(self._history) < self.stability_rounds:
            return False

        for hist_cv in self._history[-self.stability_rounds:]:
            n = len([d for d, cv in hist_cv.items() if cv < self.cv_threshold])
            if n < self.domains_required:
                return False

        return True

    def compute_consensus(
        self, parsed_params: Dict[str, ParameterSet]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute consensus values across agents.

        Numeric: median (robust to outliers)
        Categorical: mode
        """
        from collections import Counter

        consensus = {}

        for domain_id in self.domain_ids:
            domain_consensus = {}

            # Collect sub-parameter keys
            all_sub_keys = set()
            for agent_params in parsed_params.values():
                for key in agent_params.values:
                    if key.startswith(f"{domain_id}."):
                        sub_key = key.split(".", 1)[1]
                        all_sub_keys.add(sub_key)

            for sub_key in all_sub_keys:
                numeric_values = []
                categorical_values = []
                justifications = []
                uncertainties = []

                for agent_id, agent_params in parsed_params.items():
                    pv = agent_params.get(domain_id, sub_key)
                    if pv is None:
                        continue
                    try:
                        numeric_values.append(float(pv.value))
                    except (TypeError, ValueError):
                        categorical_values.append(str(pv.value))
                    if pv.justification:
                        justifications.append(f"[{agent_id}] {pv.justification}")
                    if pv.uncertainty_range:
                        uncertainties.append(pv.uncertainty_range)

                if numeric_values:
                    median_val = float(np.median(numeric_values))
                    # Uncertainty from agent spread
                    agent_q25 = float(np.percentile(numeric_values, 25))
                    agent_q75 = float(np.percentile(numeric_values, 75))
                    # Also incorporate reported uncertainty ranges
                    if uncertainties:
                        all_lows = [u[0] for u in uncertainties]
                        all_highs = [u[1] for u in uncertainties]
                        range_low = float(np.median(all_lows))
                        range_high = float(np.median(all_highs))
                    else:
                        range_low = agent_q25
                        range_high = agent_q75

                    domain_consensus[sub_key] = {
                        "value": median_val,
                        "type": "numeric",
                        "agent_spread": [agent_q25, agent_q75],
                        "uncertainty_range": [range_low, range_high],
                        "n_agents": len(numeric_values),
                        "all_values": numeric_values,
                        "justifications": justifications[:3],  # top 3
                    }
                elif categorical_values:
                    counts = Counter(categorical_values)
                    mode_val = counts.most_common(1)[0][0]
                    agreement = counts.most_common(1)[0][1] / len(categorical_values)
                    domain_consensus[sub_key] = {
                        "value": mode_val,
                        "type": "categorical",
                        "agreement_fraction": agreement,
                        "vote_distribution": dict(counts),
                        "n_agents": len(categorical_values),
                        "justifications": justifications[:3],
                    }

            consensus[domain_id] = domain_consensus

        return consensus

    def get_divergent_parameters(
        self,
        agent_params: ParameterSet,
        consensus: Dict[str, Dict[str, Any]],
        threshold_sd: float = 1.0,
    ) -> List[str]:
        """
        Identify parameters where an agent diverges >threshold_sd from consensus.

        Returns list of "domain_id.param_id" keys.
        """
        divergent = []

        for domain_id, domain_consensus in consensus.items():
            for sub_key, cons in domain_consensus.items():
                pv = agent_params.get(domain_id, sub_key)
                if pv is None:
                    continue

                if cons["type"] == "numeric":
                    try:
                        agent_val = float(pv.value)
                    except (TypeError, ValueError):
                        continue
                    all_vals = cons.get("all_values", [])
                    if len(all_vals) < 2:
                        continue
                    std = float(np.std(all_vals))
                    if std == 0:
                        continue
                    z = abs(agent_val - cons["value"]) / std
                    if z > threshold_sd:
                        divergent.append(f"{domain_id}.{sub_key}")

                elif cons["type"] == "categorical":
                    if str(pv.value) != cons["value"]:
                        divergent.append(f"{domain_id}.{sub_key}")

        return divergent

    def parameter_distance(self, params_a: ParameterSet, params_b: ParameterSet) -> float:
        """
        Compute distance between two agents' parameter sets.
        Used for critique target selection (prioritize most-divergent pairs).
        """
        all_keys = set(params_a.values.keys()) | set(params_b.values.keys())
        if not all_keys:
            return 0.0

        distances = []
        for key in all_keys:
            pv_a = params_a.values.get(key)
            pv_b = params_b.values.get(key)
            if pv_a is None or pv_b is None:
                distances.append(1.0)
                continue
            try:
                va = float(pv_a.value)
                vb = float(pv_b.value)
                denom = max(abs(va), abs(vb), 1e-10)
                distances.append(abs(va - vb) / denom)
            except (TypeError, ValueError):
                distances.append(0.0 if str(pv_a.value) == str(pv_b.value) else 1.0)

        return float(np.mean(distances)) if distances else 0.0
