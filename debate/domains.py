"""
Parameter Domain Schemas for AI ACO Design
==========================================
Defines the 12 design parameter domains that agents debate.
Each domain has a name, description, valid range, unit, and type.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class ParameterDomain:
    """A single design parameter domain with valid ranges and metadata."""
    domain_id: str
    name: str
    description: str
    sub_parameters: List["SubParameter"]

    def describe(self) -> str:
        """Human-readable description for prompt injection."""
        lines = [f"## {self.domain_id}. {self.name}", self.description, "Sub-parameters:"]
        for sp in self.sub_parameters:
            range_str = ""
            if sp.valid_range:
                range_str = f" (valid range: {sp.valid_range[0]}–{sp.valid_range[1]} {sp.unit})"
            elif sp.valid_options:
                range_str = f" (options: {', '.join(sp.valid_options)})"
            lines.append(f"  - {sp.param_id}: {sp.description}{range_str}")
        return "\n".join(lines)


@dataclass
class SubParameter:
    """A specific numeric or categorical parameter within a domain."""
    param_id: str
    description: str
    param_type: str  # "numeric", "categorical", "percentage", "ratio", "currency"
    unit: str
    valid_range: Optional[Tuple[float, float]] = None  # for numeric
    valid_options: Optional[List[str]] = None  # for categorical
    default: Optional[Any] = None


def build_domains() -> Dict[str, ParameterDomain]:
    """Construct all 12 parameter domains."""

    domains = {}

    # -----------------------------------------------------------------------
    # 1. Clinical Model
    # -----------------------------------------------------------------------
    domains["clinical_model"] = ParameterDomain(
        domain_id="1",
        name="Clinical Delivery Model",
        description=(
            "How primary care is delivered: virtual-first AI PCP with human escalation, "
            "hybrid AI+human model, or AI triage with human delivery. Specify the role "
            "of AI in clinical encounters and when humans are required."
        ),
        sub_parameters=[
            SubParameter("ai_encounter_share", "Percentage of PCP encounters handled by AI without physician involvement", "percentage", "%", (0, 100)),
            SubParameter("escalation_threshold", "Clinical criteria triggering mandatory human physician review", "categorical", "criteria_set", valid_options=["any_uncertainty", "high_acuity_only", "emergency_only", "scheduled_review"]),
            SubParameter("encounter_modality_mix", "Share of encounters that are synchronous video vs asynchronous text vs phone", "percentage", "% synchronous", (0, 100)),
            SubParameter("physical_exam_pathway", "How patients needing physical examination access in-person care", "categorical", "pathway", valid_options=["fqhc_referral", "mobile_unit", "partner_clinic", "hybrid_hub"]),
            SubParameter("ai_diagnostic_scope", "ICD-10 chapter scope AI can independently manage", "categorical", "scope", valid_options=["limited_acute", "common_chronic", "full_primary_care", "primary_plus_behavioral"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 2. Payment Structure
    # -----------------------------------------------------------------------
    domains["payment_structure"] = ParameterDomain(
        domain_id="2",
        name="Payment Structure",
        description=(
            "How the AI ACO is paid by the state Medicaid agency. Options include "
            "full capitation, global budget with growth cap, FFS with VBC overlay, "
            "or hybrid models."
        ),
        sub_parameters=[
            SubParameter("payment_model", "Primary payment mechanism", "categorical", "model", valid_options=["full_capitation", "global_budget", "ffs_plus_vbc", "hybrid_cap_ffs"]),
            SubParameter("capitation_pmpm", "Monthly per-member-per-month capitation amount", "currency", "USD", (200, 1200)),
            SubParameter("risk_sharing", "Degree of financial risk assumed by AI ACO", "categorical", "model", valid_options=["one_sided_upside", "two_sided_symmetric", "full_risk", "risk_corridor"]),
            SubParameter("minimum_savings_rate", "MSR threshold before shared savings apply", "percentage", "%", (0, 5)),
            SubParameter("shared_savings_split", "AI ACO share of savings beyond MSR", "percentage", "%", (20, 80)),
        ],
    )

    # -----------------------------------------------------------------------
    # 3. Provider Payment Rates
    # -----------------------------------------------------------------------
    domains["provider_rates"] = ParameterDomain(
        domain_id="3",
        name="Provider Payment Rates",
        description=(
            "How the AI ACO pays contracted providers (physicians, hospitals, specialists). "
            "Specify rates relative to Medicare RBRVS fee schedule."
        ),
        sub_parameters=[
            SubParameter("pcp_rate_pct_medicare", "Primary care payment as % of Medicare RBRVS", "percentage", "%", (80, 200)),
            SubParameter("specialist_rate_pct_medicare", "Specialist payment as % of Medicare RBRVS", "percentage", "%", (70, 150)),
            SubParameter("hospital_rate_pct_medicare", "Hospital inpatient/outpatient as % of Medicare DRG/APC", "percentage", "%", (80, 200)),
            SubParameter("fqhc_payment_method", "FQHC payment approach", "categorical", "method", valid_options=["pps_wrap", "pps_plus_bonus", "encounter_rate", "global_budget"]),
            SubParameter("rural_rate_adjustment", "Additional payment adjustment for rural providers", "percentage", "%", (0, 30)),
        ],
    )

    # -----------------------------------------------------------------------
    # 4. Organizational Structure
    # -----------------------------------------------------------------------
    domains["org_structure"] = ParameterDomain(
        domain_id="4",
        name="Organizational Structure",
        description=(
            "Legal and governance structure of the AI ACO. Must be non-profit and "
            "financially self-sustaining."
        ),
        sub_parameters=[
            SubParameter("legal_form", "Legal entity type", "categorical", "form", valid_options=["501c3_nonprofit", "public_benefit_corp", "cooperative", "government_entity", "public_utility"]),
            SubParameter("board_composition", "Percentage of board seats held by Medicaid beneficiaries", "percentage", "%", (10, 60)),
            SubParameter("executive_comp_cap", "Maximum executive compensation as multiple of median Medicaid income", "ratio", "x median", (3, 20)),
            SubParameter("conversion_prohibition", "Structural prohibition on for-profit conversion", "categorical", "mechanism", valid_options=["charter_lock", "state_law", "cy_pres_doctrine", "none"]),
            SubParameter("surplus_distribution", "How operating surplus is distributed", "categorical", "method", valid_options=["community_reinvestment", "provider_bonus", "rate_reduction", "reserve_build"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 5. Regulatory Pathway
    # -----------------------------------------------------------------------
    domains["regulatory_pathway"] = ParameterDomain(
        domain_id="5",
        name="Regulatory Pathway",
        description=(
            "Federal and state regulatory authorization for the AI ACO. Must specify "
            "exact waiver type and legal authorities."
        ),
        sub_parameters=[
            SubParameter("federal_authority", "Federal authorization mechanism", "categorical", "authority", valid_options=["section_1115", "section_1915b", "state_plan_amendment", "cmmi_model"]),
            SubParameter("ai_licensure_model", "How AI clinical practice is legally authorized", "categorical", "model", valid_options=["physician_supervised", "regulatory_sandbox", "new_provider_category", "fda_authorized_device"]),
            SubParameter("implementation_timeline", "Months from waiver application to first enrollment", "numeric", "months", (12, 48)),
            SubParameter("pilot_geography", "Initial pilot scope", "categorical", "scope", valid_options=["single_county", "single_metro", "statewide", "multi_state"]),
            SubParameter("sunset_provision", "Automatic expiration requiring reauthorization", "numeric", "years", (3, 10)),
        ],
    )

    # -----------------------------------------------------------------------
    # 6. Quality Framework
    # -----------------------------------------------------------------------
    domains["quality_framework"] = ParameterDomain(
        domain_id="6",
        name="Quality Measurement Framework",
        description=(
            "How clinical quality is measured and incentivized. Must include both "
            "traditional HEDIS-type measures and AI-specific quality metrics."
        ),
        sub_parameters=[
            SubParameter("hedis_measures_count", "Number of HEDIS measures tracked and reported", "numeric", "measures", (10, 50)),
            SubParameter("patient_reported_outcomes", "Whether PRO measures (PHQ-9, SF-12, etc.) are mandatory", "categorical", "requirement", valid_options=["mandatory_quarterly", "mandatory_annual", "optional", "none"]),
            SubParameter("ai_safety_metrics", "AI-specific safety measures (e.g., escalation rate, override rate)", "categorical", "inclusion", valid_options=["mandatory_public", "mandatory_internal", "optional", "none"]),
            SubParameter("quality_withhold_pct", "Percentage of capitation withheld pending quality performance", "percentage", "%", (0, 10)),
            SubParameter("health_equity_reporting", "Stratified quality reporting by race/ethnicity/language", "categorical", "requirement", valid_options=["mandatory_public", "mandatory_cms", "voluntary", "none"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 7. AI Clinical Decision Architecture
    # -----------------------------------------------------------------------
    domains["ai_architecture"] = ParameterDomain(
        domain_id="7",
        name="AI Clinical Decision Architecture",
        description=(
            "Technical architecture of the AI clinical decision system. "
            "Multi-model ensemble vs single model with safety layers."
        ),
        sub_parameters=[
            SubParameter("architecture_type", "AI system architecture", "categorical", "type", valid_options=["multi_model_ensemble", "single_model_safety_layer", "chain_of_thought_verified", "retrieval_augmented"]),
            SubParameter("model_count", "Number of independent AI models in ensemble", "numeric", "models", (1, 7)),
            SubParameter("safety_layer_type", "Safety mechanism for high-risk clinical decisions", "categorical", "type", valid_options=["deterministic_rules", "world_model_simulation", "confidence_threshold", "multi_layer"]),
            SubParameter("clinical_knowledge_update", "Frequency of clinical knowledge base updates", "categorical", "frequency", valid_options=["real_time", "weekly", "monthly", "quarterly"]),
            SubParameter("explainability_requirement", "Level of AI decision explainability to patients/providers", "categorical", "level", valid_options=["full_reasoning_chain", "key_factors_only", "confidence_score_only", "none"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 8. Human Oversight Model
    # -----------------------------------------------------------------------
    domains["human_oversight"] = ParameterDomain(
        domain_id="8",
        name="Human Oversight Model",
        description=(
            "Physician and clinical staff oversight of AI clinical decisions. "
            "Must specify supervision ratios, review processes, and escalation."
        ),
        sub_parameters=[
            SubParameter("supervision_ratio", "Maximum AI encounters per supervising physician per hour", "ratio", "encounters/physician/hour", (5, 200)),
            SubParameter("synchronous_review_pct", "Percentage of AI encounters reviewed in real-time by physician", "percentage", "%", (1, 100)),
            SubParameter("retrospective_audit_pct", "Percentage of AI encounters audited retrospectively", "percentage", "%", (1, 50)),
            SubParameter("mandatory_physician_encounters", "Encounter types that always require physician", "categorical", "scope", valid_options=["new_patient_only", "new_plus_complex", "all_diagnostic", "scheduled_periodic"]),
            SubParameter("patient_escalation_mechanism", "How patients request human physician involvement", "categorical", "mechanism", valid_options=["one_click_anytime", "callback_within_1hr", "scheduled_appointment", "emergency_only"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 9. SDOH Integration
    # -----------------------------------------------------------------------
    domains["sdoh_integration"] = ParameterDomain(
        domain_id="9",
        name="Social Determinants of Health Integration",
        description=(
            "Community health worker deployment, social services referral, "
            "and SDOH screening/intervention budget."
        ),
        sub_parameters=[
            SubParameter("chw_ratio", "Community health workers per 1,000 enrolled members", "ratio", "CHWs/1000", (0.5, 10)),
            SubParameter("sdoh_screening_frequency", "SDOH screening interval for all members", "categorical", "frequency", valid_options=["at_enrollment", "annual", "semi_annual", "trigger_based"]),
            SubParameter("social_services_budget_pmpm", "Monthly per-member budget for social services referrals/payments", "currency", "USD", (0, 50)),
            SubParameter("housing_food_direct_spend", "Whether AI ACO directly pays for housing/food assistance", "categorical", "policy", valid_options=["yes_budgeted", "referral_only", "partnership_funded", "no"]),
            SubParameter("community_partnership_model", "How AI ACO partners with community organizations", "categorical", "model", valid_options=["contracted_network", "capitated_cbo", "grant_funded", "informal_referral"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 10. Rural/Urban Design Variants
    # -----------------------------------------------------------------------
    domains["rural_urban"] = ParameterDomain(
        domain_id="10",
        name="Rural/Urban Design Variants",
        description=(
            "How the AI ACO adapts for rural vs urban populations, addressing "
            "broadband gaps, provider shortages, and transportation barriers."
        ),
        sub_parameters=[
            SubParameter("rural_delivery_model", "Primary care delivery model for rural areas", "categorical", "model", valid_options=["virtual_plus_mobile", "hub_and_spoke", "fqhc_partnership", "telehealth_kiosk"]),
            SubParameter("broadband_solution", "Solution for members without home broadband", "categorical", "solution", valid_options=["subsidized_hotspot", "community_access_point", "phone_only_pathway", "hybrid_mail_phone"]),
            SubParameter("rural_specialist_access", "How rural members access specialty care", "categorical", "method", valid_options=["etelehealth", "transportation_assistance", "specialist_circuit_riders", "urban_referral"]),
            SubParameter("critical_access_hospital_policy", "Policy for rural/critical access hospitals", "categorical", "policy", valid_options=["preserved_payment", "enhanced_payment", "volume_guarantee", "partnership_model"]),
            SubParameter("telehealth_infrastructure_investment", "Annual investment in rural telehealth infrastructure per rural member", "currency", "USD", (0, 200)),
        ],
    )

    # -----------------------------------------------------------------------
    # 11. Anti-Monopoly Provisions
    # -----------------------------------------------------------------------
    domains["anti_monopoly"] = ParameterDomain(
        domain_id="11",
        name="Anti-Monopoly and Market Design",
        description=(
            "How the AI ACO negotiates with and constrains monopoly providers. "
            "Address consolidated hospital systems, any-willing-provider laws, "
            "and reference pricing."
        ),
        sub_parameters=[
            SubParameter("rate_negotiation_approach", "How provider rates are set when providers have market power", "categorical", "approach", valid_options=["medicare_reference", "competitive_bidding", "rate_regulation", "all_payer_rate_setting"]),
            SubParameter("any_willing_provider", "Whether any licensed provider can join network at standard rates", "categorical", "policy", valid_options=["yes_mandatory", "yes_with_quality_floor", "selective_contracting", "hybrid"]),
            SubParameter("monopoly_provider_policy", "Policy for sole community providers or monopoly hospital systems", "categorical", "policy", valid_options=["must_contract_at_cap", "state_mediated_rate", "federal_rate_floor_ceiling", "bypass_via_telehealth"]),
            SubParameter("site_of_service_steering", "Whether AI ACO directs patients to lower-cost appropriate sites", "categorical", "policy", valid_options=["active_steering", "information_only", "incentive_based", "no_steering"]),
            SubParameter("network_exclusivity", "Whether members can go out-of-network", "categorical", "policy", valid_options=["closed_network", "open_with_cost_sharing", "open_for_specialists", "fully_open"]),
        ],
    )

    # -----------------------------------------------------------------------
    # 12. Ethical Governance
    # -----------------------------------------------------------------------
    domains["ethical_governance"] = ParameterDomain(
        domain_id="12",
        name="Ethical Governance and Accountability",
        description=(
            "Structural governance provisions to prevent corporate capture, "
            "ensure accountability, and maintain ethical AI operation."
        ),
        sub_parameters=[
            SubParameter("ai_audit_frequency", "Independent algorithmic audit frequency", "categorical", "frequency", valid_options=["continuous_automated", "quarterly", "semi_annual", "annual"]),
            SubParameter("bias_audit_stratification", "Dimensions for mandatory bias auditing", "categorical", "dimensions", valid_options=["race_ethnicity_only", "race_gender_age", "race_gender_age_disability_language", "all_protected_classes"]),
            SubParameter("transparency_level", "Public disclosure of AI performance data", "categorical", "level", valid_options=["full_public_dashboard", "annual_public_report", "regulator_only", "proprietary"]),
            SubParameter("patient_data_rights", "Patient control over their health data", "categorical", "rights", valid_options=["full_portability_deletion", "portability_only", "access_only", "hipaa_minimum"]),
            SubParameter("independent_ethics_board", "Whether an independent ethics board has authority to halt AI operations", "categorical", "authority", valid_options=["binding_halt_authority", "advisory_with_public_report", "advisory_only", "none"]),
        ],
    )

    return domains


def get_domain_descriptions() -> str:
    """Get formatted descriptions of all 12 domains for prompt injection."""
    domains = build_domains()
    return "\n\n".join(d.describe() for d in domains.values())
