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

    # -------------------------------------------------------------------
    # Delphi convergence metrics
    # -------------------------------------------------------------------

    def compute_delphi_metrics(
        self, parsed_params: Dict[str, ParameterSet]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute Delphi-style summary statistics for each domain.

        Returns dict of domain_id -> {
            sub_param_key -> {
                "type": "numeric" | "categorical",
                # numeric fields:
                "median": float, "q1": float, "q3": float, "iqr": float,
                "values_by_agent": {agent_id: value},
                # categorical fields:
                "mode": str, "mode_pct": float, "vote_distribution": {val: count},
                "votes_by_agent": {agent_id: value},
            }
        }
        """
        from collections import Counter

        metrics: Dict[str, Dict[str, Any]] = {}

        for domain_id in self.domain_ids:
            domain_metrics: Dict[str, Any] = {}

            # Collect sub-parameter keys for this domain
            all_sub_keys: set = set()
            for agent_params in parsed_params.values():
                for key in agent_params.values:
                    if key.startswith(f"{domain_id}."):
                        all_sub_keys.add(key.split(".", 1)[1])

            for sub_key in sorted(all_sub_keys):
                numeric_by_agent: Dict[str, float] = {}
                categorical_by_agent: Dict[str, str] = {}

                for agent_id, agent_params in parsed_params.items():
                    pv = agent_params.get(domain_id, sub_key)
                    if pv is None:
                        continue
                    try:
                        numeric_by_agent[agent_id] = float(pv.value)
                    except (TypeError, ValueError):
                        categorical_by_agent[agent_id] = str(pv.value)

                if len(numeric_by_agent) >= 2:
                    vals = list(numeric_by_agent.values())
                    q1 = float(np.percentile(vals, 25))
                    q3 = float(np.percentile(vals, 75))
                    domain_metrics[sub_key] = {
                        "type": "numeric",
                        "median": float(np.median(vals)),
                        "q1": q1,
                        "q3": q3,
                        "iqr": q3 - q1,
                        "values_by_agent": numeric_by_agent,
                    }
                elif len(categorical_by_agent) >= 2:
                    counts = Counter(categorical_by_agent.values())
                    mode_val, mode_count = counts.most_common(1)[0]
                    total = len(categorical_by_agent)
                    domain_metrics[sub_key] = {
                        "type": "categorical",
                        "mode": mode_val,
                        "mode_pct": mode_count / total,
                        "vote_distribution": dict(counts),
                        "votes_by_agent": categorical_by_agent,
                    }

            metrics[domain_id] = domain_metrics

        return metrics

    def compute_delphi_metrics_with_previous(
        self,
        current_params: Dict[str, ParameterSet],
        previous_params: Optional[Dict[str, ParameterSet]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute Delphi metrics and annotate with change-from-previous info.

        If previous_params is provided, each numeric sub-param also gets:
            "prev_iqr": float
            "iqr_decreased": bool
        And each categorical sub-param also gets:
            "prev_mode_pct": float
        """
        metrics = self.compute_delphi_metrics(current_params)

        if previous_params is not None:
            prev_metrics = self.compute_delphi_metrics(previous_params)
            for domain_id, domain_m in metrics.items():
                prev_domain = prev_metrics.get(domain_id, {})
                for sub_key, sub_m in domain_m.items():
                    prev_sub = prev_domain.get(sub_key)
                    if prev_sub is None:
                        continue
                    if sub_m["type"] == "numeric" and prev_sub["type"] == "numeric":
                        sub_m["prev_iqr"] = prev_sub["iqr"]
                        sub_m["iqr_decreased"] = sub_m["iqr"] <= prev_sub["iqr"]
                    elif sub_m["type"] == "categorical" and prev_sub["type"] == "categorical":
                        sub_m["prev_mode_pct"] = prev_sub["mode_pct"]

        return metrics

    def is_delphi_converged(
        self,
        current_metrics: Dict[str, Dict[str, Any]],
        round_num: int,
        categorical_agreement_threshold: float = 0.75,
    ) -> bool:
        """
        Check Delphi convergence.

        A domain is converged when:
        - Numeric sub-params: IQR decreased or stable vs previous round
          for >= stability_rounds consecutive rounds
        - Categorical sub-params: >= categorical_agreement_threshold agreement

        Overall: >= domains_required domains converged.
        """
        if round_num < self.stability_rounds:
            return False

        converged_count = 0
        for domain_id, domain_m in current_metrics.items():
            domain_converged = self._is_domain_delphi_converged(
                domain_m, categorical_agreement_threshold
            )
            if domain_converged:
                converged_count += 1

        return converged_count >= self.domains_required

    def get_delphi_converged_domains(
        self,
        current_metrics: Dict[str, Dict[str, Any]],
        categorical_agreement_threshold: float = 0.75,
    ) -> List[str]:
        """Return list of domain_ids that meet Delphi convergence criteria."""
        converged = []
        for domain_id, domain_m in current_metrics.items():
            if self._is_domain_delphi_converged(
                domain_m, categorical_agreement_threshold
            ):
                converged.append(domain_id)
        return converged

    def _is_domain_delphi_converged(
        self,
        domain_metrics: Dict[str, Any],
        categorical_agreement_threshold: float = 0.75,
    ) -> bool:
        """Check if a single domain meets Delphi convergence criteria."""
        if not domain_metrics:
            return False

        sub_converged = 0
        sub_total = 0

        for sub_key, sub_m in domain_metrics.items():
            sub_total += 1
            if sub_m["type"] == "numeric":
                # Converged if IQR decreased or stable (requires prev_iqr annotation)
                if "iqr_decreased" in sub_m:
                    if sub_m["iqr_decreased"]:
                        sub_converged += 1
                else:
                    # First round with metrics — not converged yet
                    pass
            elif sub_m["type"] == "categorical":
                if sub_m["mode_pct"] >= categorical_agreement_threshold:
                    sub_converged += 1

        # Domain converged if majority of sub-params converged
        return sub_total > 0 and sub_converged >= (sub_total / 2)

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
