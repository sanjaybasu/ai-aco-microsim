"""
PSA Parameter Distributions for AI ACO Microsimulation
======================================================
Extends the PSAParameters pattern from ncqa_medicaid_vbc for the
5-channel AI ACO microsimulation. All parameters sourced from
public data (MACPAC, MEPS, NCQA, CMS, published literature).
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class StateParameters:
    """State-level Medicaid parameters from public sources."""
    state: str
    medicaid_pmpm_adult: float  # MACPAC MACStats
    mco_admin_rate: float  # CMS MLR reports (~8-17%)
    mco_profit_margin: float  # SOA (0.35-3.15%)
    pcp_supply_per_100k: float  # HRSA AHRF
    broadband_penetration: float  # FCC + ACS (% of Medicaid pop)
    fqhc_penetration: float  # HRSA UDS (% Medicaid enrollees)
    hedis_composite: float  # NCQA state profiles (stars)
    medicaid_enrollment: int  # CMS enrollment data


# State-level parameters for 17 Medicaid expansion states with ACS PUMS coverage
STATE_PARAMS: Dict[str, StateParameters] = {
    "AR": StateParameters("AR", 430, 0.12, 0.015, 31, 0.71, 0.22, 3.2, 912000),
    "AZ": StateParameters("AZ", 520, 0.10, 0.020, 38, 0.82, 0.28, 3.5, 2150000),
    "GA": StateParameters("GA", 380, 0.13, 0.018, 33, 0.76, 0.20, 3.1, 2100000),
    "IN": StateParameters("IN", 490, 0.11, 0.015, 36, 0.79, 0.25, 3.4, 1650000),
    "KY": StateParameters("KY", 510, 0.12, 0.016, 34, 0.74, 0.30, 3.3, 1450000),
    "LA": StateParameters("LA", 470, 0.13, 0.017, 30, 0.72, 0.26, 3.1, 1750000),
    "ME": StateParameters("ME", 550, 0.09, 0.012, 42, 0.81, 0.35, 3.7, 380000),
    "MI": StateParameters("MI", 480, 0.11, 0.014, 37, 0.80, 0.27, 3.4, 2700000),
    "MT": StateParameters("MT", 560, 0.10, 0.013, 28, 0.68, 0.32, 3.5, 290000),
    "NH": StateParameters("NH", 530, 0.09, 0.011, 44, 0.87, 0.30, 3.8, 210000),
    "NM": StateParameters("NM", 500, 0.12, 0.015, 26, 0.70, 0.38, 3.2, 830000),
    "OH": StateParameters("OH", 470, 0.12, 0.016, 39, 0.81, 0.24, 3.4, 3200000),
    "SC": StateParameters("SC", 410, 0.13, 0.018, 32, 0.75, 0.21, 3.1, 1250000),
    "SD": StateParameters("SD", 540, 0.10, 0.014, 25, 0.67, 0.33, 3.3, 135000),
    "UT": StateParameters("UT", 460, 0.10, 0.015, 35, 0.86, 0.22, 3.6, 420000),
    "VA": StateParameters("VA", 500, 0.11, 0.015, 40, 0.83, 0.23, 3.5, 1850000),
    "WI": StateParameters("WI", 490, 0.10, 0.013, 41, 0.84, 0.28, 3.6, 1200000),
}


class AIACOPSAParameters:
    """
    Probabilistic parameter distributions for the AI ACO microsimulation.

    Extends the PSAParameters pattern from ncqa_medicaid_vbc.
    All distributions parameterized from published sources.
    """

    def __init__(self):
        # -----------------------------------------------------------
        # Channel 1: Access / Eligibility
        # -----------------------------------------------------------
        # Digital access probability by demographic group
        # Source: Pew Research 2024 digital divide; FCC broadband maps
        self.p_digital_access = {
            "white_metro": stats.beta(85, 15),     # ~85%
            "white_nonmetro": stats.beta(72, 28),   # ~72%
            "black_metro": stats.beta(78, 22),      # ~78%
            "black_nonmetro": stats.beta(62, 38),   # ~62%
            "hispanic_metro": stats.beta(74, 26),   # ~74%
            "hispanic_nonmetro": stats.beta(58, 42), # ~58%
            "aian_metro": stats.beta(68, 32),       # ~68%
            "aian_nonmetro": stats.beta(45, 55),    # ~45%
        }

        # Language access (LEP = limited English proficiency)
        # Source: ACS 2022 language spoken at home by insurance type
        self.p_lep = {
            "white": stats.beta(5, 95),       # ~5%
            "black": stats.beta(8, 92),       # ~8%
            "hispanic": stats.beta(42, 58),   # ~42%
            "aian": stats.beta(15, 85),       # ~15%
        }

        # AI multilingual capability (probability LEP patient can be served)
        # Source: Published AI translation benchmarks
        self.p_ai_language_success = stats.beta(82, 18)  # ~82%

        # -----------------------------------------------------------
        # Channel 2: Engagement Cascade
        # -----------------------------------------------------------
        # Status quo MCO engagement rates by risk tier
        # Source: Vasan et al. Health Serv Res 2020; AHRQ NHQDR 2023
        self.sq_outreach = {
            "low": stats.beta(70, 30),
            "rising": stats.beta(75, 25),
            "high": stats.beta(80, 20),
        }
        self.sq_agreement = {
            "low": stats.beta(40, 60),
            "rising": stats.beta(55, 45),
            "high": stats.beta(65, 35),
        }
        self.sq_engagement = {
            "low": stats.beta(60, 40),
            "rising": stats.beta(65, 35),
            "high": stats.beta(70, 30),
        }
        self.sq_adherence = {
            "low": stats.beta(50, 50),
            "rising": stats.beta(55, 45),
            "high": stats.beta(60, 40),
        }

        # AI ACO engagement multipliers (relative to SQ)
        # Source: Published telemedicine/virtual-first engagement literature
        self.ai_outreach_multiplier = stats.gamma(a=25, scale=0.048)  # mean 1.20
        self.ai_agreement_multiplier = stats.gamma(a=25, scale=0.052)  # mean 1.30
        self.ai_engagement_multiplier = stats.gamma(a=25, scale=0.044)  # mean 1.10
        self.ai_adherence_multiplier = stats.gamma(a=25, scale=0.044)  # mean 1.10

        # Racial engagement differential (Black/Hispanic vs White)
        # Source: AHRQ NHQDR 2023
        self.engagement_racial_penalty = {
            "white": 0.0,
            "black": stats.beta(15, 85),    # ~15% lower engagement
            "hispanic": stats.beta(12, 88), # ~12% lower
            "aian": stats.beta(20, 80),     # ~20% lower
        }

        # AI ACO reduces racial engagement gap by this fraction
        # Source: Published telehealth equity evidence (multilingual, 24/7, no transport)
        self.ai_equity_gap_reduction = stats.beta(25, 75)  # ~25%

        # -----------------------------------------------------------
        # Channel 3: Utilization & Cost
        # -----------------------------------------------------------
        # Baseline utilization rates per 1,000 person-years by risk tier
        # Source: MEPS 2022 + HCUP 2022 for Medicaid adults
        self.baseline_hosp_rate = {
            "low": stats.gamma(a=16, scale=5),      # mean 80/1000 PY
            "rising": stats.gamma(a=25, scale=10),    # mean 250/1000 PY
            "high": stats.gamma(a=25, scale=20),      # mean 500/1000 PY
        }
        self.baseline_ed_rate = {
            "low": stats.gamma(a=25, scale=16),      # mean 400/1000 PY
            "rising": stats.gamma(a=25, scale=36),    # mean 900/1000 PY
            "high": stats.gamma(a=25, scale=60),      # mean 1500/1000 PY
        }
        self.baseline_pcp_rate = {
            "low": stats.gamma(a=25, scale=100),     # mean 2500/1000 PY
            "rising": stats.gamma(a=25, scale=160),   # mean 4000/1000 PY
            "high": stats.gamma(a=25, scale=240),     # mean 6000/1000 PY
        }

        # AI ACO intervention effect on utilization (relative risk reductions)
        # Source: Published VBC/ACO evaluation meta-analyses
        # Conservative: MSSP saves 1-3% total cost; Medicaid ACOs mixed
        self.ai_hosp_rr_reduction = {
            "low": stats.beta(15, 85),    # ~15% RR reduction
            "rising": stats.beta(25, 75),  # ~25% RR reduction
            "high": stats.beta(20, 80),    # ~20% RR reduction
        }
        self.ai_ed_rr_reduction = {
            "low": stats.beta(12, 88),    # ~12%
            "rising": stats.beta(20, 80),  # ~20%
            "high": stats.beta(15, 85),    # ~15%
        }
        self.ai_pcp_increase = stats.beta(15, 85)  # ~15% increase in PCP utilization (intended)

        # Unit costs (2024 USD)
        # Source: HCUP, MEPS for Medicaid payer
        self.cost_hospitalization = stats.gamma(a=100, scale=100)  # mean $10,000
        self.cost_ed = stats.gamma(a=49, scale=14.3)               # mean $700
        self.cost_pcp = stats.gamma(a=25, scale=5)                 # mean $125
        self.cost_pharmacy_pmpm = stats.gamma(a=25, scale=8)        # mean $200

        # -----------------------------------------------------------
        # Channel 4: Quality (HEDIS)
        # -----------------------------------------------------------
        # Status quo HEDIS gap closure rate (fraction of open gaps closed per year)
        # Source: NCQA State of Healthcare Quality Report
        self.sq_hedis_gap_closure = stats.beta(35, 65)  # ~35%

        # AI ACO HEDIS gap closure rate
        # Source: Published AI proactive outreach evidence
        self.ai_hedis_gap_closure = stats.beta(50, 50)  # ~50%

        # Racial differential in gap closure (Black vs White)
        self.hedis_racial_gap = stats.beta(12, 88)  # ~12pp gap

        # AI reduces racial HEDIS gap by this fraction
        self.ai_hedis_equity_improvement = stats.beta(20, 80)  # ~20%

        # -----------------------------------------------------------
        # Channel 5: Equity (Detection/Documentation)
        # -----------------------------------------------------------
        # Detection/certification base rates by race (Obermeyer et al. Science 2019)
        # Point estimates with SD for sampling
        self.p_detect_sd = 0.06
        self.p_cert_sd = 0.05

        # AI ACO detection improvement (proportional gap closure to ceiling=0.98)
        # Source: Derived from ACS PUMS analysis of claims visibility
        self.ai_detection_gap_closure = stats.beta(35, 65)  # ~35%

        # AI ACO certification bypass fraction (no physician cert needed)
        self.ai_cert_bypass = stats.beta(80, 20)  # ~80% of cert requirements eliminated

        # -----------------------------------------------------------
        # Administrative costs
        # -----------------------------------------------------------
        # Status quo MCO admin rate
        self.sq_admin_rate = stats.beta(8, 92)  # ~8% (of premium)

        # AI ACO admin rate (major innovation claim)
        self.ai_admin_rate = stats.beta(3, 97)  # ~3% (of premium)

        # -----------------------------------------------------------
        # AI encounter share (PSA distribution)
        # -----------------------------------------------------------
        # Fraction of total encounters handled by AI-first virtual care.
        # Consensus design: 58% (eTable 4). Beta distribution parameterized
        # to reflect debate uncertainty (pessimistic minority: 40%; optimistic: 72%).
        # Population-level mean; individual-level share conditioned on digital
        # access in channels.py Channel 3.
        # Source: Multi-agent Delphi consensus (Round 2, CV = 0.12).
        self.ai_encounter_share = stats.beta(a=30, b=22)  # mean ~0.577, SD ~0.058

        # -----------------------------------------------------------
        # Provider reimbursement → network adequacy
        # -----------------------------------------------------------
        # Provider rate as % of Medicare RBRVS
        # Source: Consensus design = 125% PCP, 110% hospital
        # Current Medicaid average ~75% (MACPAC MACStats 2024)
        # Affects referral completion for the non-AI care pathway
        self.provider_rate_pct_medicare = 125.0  # default; overridable per scenario

        # -----------------------------------------------------------
        # Financial model
        # -----------------------------------------------------------
        # Risk distribution (fraction of population)
        self.risk_dist_low = stats.beta(60, 40)      # ~60%
        self.risk_dist_rising = stats.beta(25, 75)    # ~25%
        # high = 1 - low - rising

    def sample(self, state: str = "OH") -> Dict[str, Any]:
        """
        Draw one complete parameter sample for a single PSA iteration.

        Returns flat dict of parameter values for use in simulation.
        """
        sp = STATE_PARAMS.get(state, STATE_PARAMS["OH"])

        # Digital access
        digital_access = {}
        for key, dist in self.p_digital_access.items():
            digital_access[key] = np.clip(dist.rvs(), 0.30, 0.99)

        # Engagement cascade (status quo)
        sq_cascade = {}
        for tier in ["low", "rising", "high"]:
            sq_cascade[tier] = {
                "outreach": np.clip(self.sq_outreach[tier].rvs(), 0.40, 0.95),
                "agreement": np.clip(self.sq_agreement[tier].rvs(), 0.20, 0.80),
                "engagement": np.clip(self.sq_engagement[tier].rvs(), 0.30, 0.90),
                "adherence": np.clip(self.sq_adherence[tier].rvs(), 0.30, 0.80),
            }

        # AI ACO multipliers
        ai_multipliers = {
            "outreach": np.clip(self.ai_outreach_multiplier.rvs(), 1.0, 1.5),
            "agreement": np.clip(self.ai_agreement_multiplier.rvs(), 1.0, 1.6),
            "engagement": np.clip(self.ai_engagement_multiplier.rvs(), 1.0, 1.3),
            "adherence": np.clip(self.ai_adherence_multiplier.rvs(), 1.0, 1.3),
        }

        # Utilization
        baseline_util = {}
        ai_rr = {}
        for tier in ["low", "rising", "high"]:
            baseline_util[tier] = {
                "hosp": np.clip(self.baseline_hosp_rate[tier].rvs(), 20, 800),
                "ed": np.clip(self.baseline_ed_rate[tier].rvs(), 100, 2500),
                "pcp": np.clip(self.baseline_pcp_rate[tier].rvs(), 1000, 8000),
            }
            ai_rr[tier] = {
                "hosp": np.clip(self.ai_hosp_rr_reduction[tier].rvs(), 0.05, 0.40),
                "ed": np.clip(self.ai_ed_rr_reduction[tier].rvs(), 0.05, 0.35),
            }

        # Costs
        costs = {
            "hosp": np.clip(self.cost_hospitalization.rvs(), 6000, 18000),
            "ed": np.clip(self.cost_ed.rvs(), 400, 1200),
            "pcp": np.clip(self.cost_pcp.rvs(), 80, 200),
            "pharmacy_pmpm": np.clip(self.cost_pharmacy_pmpm.rvs(), 100, 400),
        }

        # Risk distribution (ensure all positive and sum to 1)
        low_pct = np.clip(self.risk_dist_low.rvs(), 0.50, 0.70)
        rising_pct = np.clip(self.risk_dist_rising.rvs(), 0.18, 0.32)
        high_pct = max(0.05, 1.0 - low_pct - rising_pct)
        # Renormalize
        total = low_pct + rising_pct + high_pct
        low_pct /= total
        rising_pct /= total
        high_pct /= total

        # Quality
        sq_hedis = np.clip(self.sq_hedis_gap_closure.rvs(), 0.20, 0.55)
        ai_hedis = np.clip(self.ai_hedis_gap_closure.rvs(), 0.30, 0.70)

        # Admin
        sq_admin = np.clip(self.sq_admin_rate.rvs(), 0.06, 0.17)
        ai_admin = np.clip(self.ai_admin_rate.rvs(), 0.01, 0.06)

        # Detection/certification (equity channel)
        ai_detect_closure = np.clip(self.ai_detection_gap_closure.rvs(), 0.15, 0.60)
        ai_cert_bypass = np.clip(self.ai_cert_bypass.rvs(), 0.50, 0.95)

        return {
            "state": state,
            "pmpm_baseline": sp.medicaid_pmpm_adult,
            "digital_access": digital_access,
            "sq_cascade": sq_cascade,
            "ai_multipliers": ai_multipliers,
            "baseline_util": baseline_util,
            "ai_rr": ai_rr,
            "costs": costs,
            "risk_dist": {"low": low_pct, "rising": rising_pct, "high": high_pct},
            "sq_hedis_closure": sq_hedis,
            "ai_hedis_closure": ai_hedis,
            "sq_admin_rate": sq_admin,
            "ai_admin_rate": ai_admin,
            "ai_detect_closure": ai_detect_closure,
            "ai_cert_bypass": ai_cert_bypass,
            "hedis_racial_gap": np.clip(self.hedis_racial_gap.rvs(), 0.05, 0.25),
            "ai_hedis_equity_improvement": np.clip(self.ai_hedis_equity_improvement.rvs(), 0.10, 0.40),
            "ai_pcp_increase": np.clip(self.ai_pcp_increase.rvs(), 0.05, 0.30),
            "engagement_racial_penalties": {
                race: np.clip(dist.rvs(), 0.05, 0.30) if isinstance(dist, stats.rv_continuous) else 0.0
                for race, dist in self.engagement_racial_penalty.items()
            },
            "ai_equity_gap_reduction": np.clip(self.ai_equity_gap_reduction.rvs(), 0.10, 0.50),
            "provider_rate_pct_medicare": self.provider_rate_pct_medicare,
            # Draw AI encounter share from PSA distribution (mean ~0.58)
            # Individual-level share is conditioned on digital access in channels.py
            "ai_encounter_share": float(np.clip(self.ai_encounter_share.rvs(), 0.35, 0.80)),
        }
