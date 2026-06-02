# Online Appendix

## eAppendix A. Multi-Agent Debate: Expert Personas and Protocol

### eTable 1. Expert Personas

| Agent | Persona | System Prompt Core | Hard Constraints |
|---|---|---|---|
| A1: Health Economist | Arrow/Krugman market failure framework; information asymmetry in healthcare markets | All cost assumptions must cite evidence; must address moral hazard and adverse selection | No designs that increase total cost to taxpayer |
| A2: Medicaid Regulator | CMS/state Medicaid director; 1115 waiver expertise | Must specify legal pathway and waiver authority for every design element | Must comply with existing federal Medicaid statute or identify specific waivers |
| A3: Patient Advocate | Medicaid beneficiary perspective; emphasis on access, dignity, cultural competency | Must address digital divide and language access; no designs that reduce patient choice | No involuntary enrollment or penalty for human provider preference |
| A4: Primary Care Physician | Board-certified internist practicing in FQHC setting | Must address clinical safety, diagnostic accuracy, and escalation protocols | No AI-only encounters for new symptoms, mental health crises, or high-acuity conditions |
| A5: FQHC Operator | Multi-site FQHC CEO; 340B and HRSA funding expertise | Must be financially viable for safety-net providers; preserve FQHC funding streams | Provider rates must exceed cost of care delivery |
| A6: Health System Ethicist | AI ethics and health equity; informed consent and algorithmic fairness | Must address bias, transparency, and governance; community representation required | Mandatory algorithmic bias auditing; beneficiary governance representation |
| A7: Actuary | MAAA/FSA; Medicaid risk corridors and actuarial modeling | Must demonstrate actuarial soundness with specific reserve and reinsurance requirements | Medical loss ratio ≥ 90%; adequate reserves for catastrophic risk |
| A8: Health Services Researcher | Value-based care and population health; implementation science | Must cite empirical evidence for all intervention effect assumptions | Effect sizes must be within published literature ranges |

### Persona Justification

The 8 personas were selected to represent the critical perspectives needed to evaluate whether an AI-driven ACO could safely improve Medicaid patient outcomes:

- **Clinical safety** (A4: Primary Care Physician) — Can AI safely manage primary care encounters? What conditions require human escalation?
- **Patient experience and access** (A3: Patient Advocate) — Will patients accept AI-delivered care? How does the digital divide affect equity?
- **Safety-net viability** (A5: FQHC Operator) — Can the model sustain safety-net infrastructure and provider employment?
- **Financial soundness** (A7: Actuary) — Is the model actuarially viable under Medicaid capitation rates?
- **Regulatory pathway** (A2: Medicaid Regulator) — What legal authority enables this model?
- **Ethical governance** (A6: Health System Ethicist) — How should algorithmic bias be monitored? What oversight structures are needed?
- **Evidence standards** (A8: Health Services Researcher) — Are the assumed effect sizes supported by published evidence?
- **Economic framework** (A1: Health Economist) — Does the model address the underlying market failure, or merely shift costs?

### Debate Protocol Details

**Round 0**: Each agent independently generated a complete AI ACO design specification across 12 parameter domains in structured JSON format, including specific numeric values, units, justifications, uncertainty ranges, and key assumptions.

**Rounds 1–2 (Delphi feedback)**: Each agent received anonymized group summary statistics — median, interquartile range (IQR), and percent agreement for each sub-parameter — with their own position highlighted as inside or outside the IQR. Agents outside the IQR were required to provide outlier justifications or revise toward the group median. All agents produced complete re-rated proposals across all 12 domains.

**Convergence metric**: Coefficient of variation (CV) of quantitative parameter values across all 8 agents, computed per domain. Categorical parameters assessed by percent agreement (mode fraction). Domain-level Delphi convergence required IQR stability or decrease for numeric parameters and ≥75% agreement for categorical parameters, with a majority of sub-parameters meeting these criteria.

**Stopping criteria**: ≥10 of 12 domains meeting Delphi convergence criteria for 2 consecutive rounds, or a maximum of 12 rounds. The process converged at Round 2 (3 total rounds).

### Minority Reports and Scenario Derivation

Agents diverging by more than 1 standard deviation from consensus on any sub-parameter submitted structured minority reports. Each report identified (a) the specific sub-parameter on which the agent dissented, (b) the agent's preferred value with justification, and (c) the direction (higher or lower) of the dissent. Seven of 8 agents filed minority reports; the patient-advocate agent had the most divergent parameters (27 of 60 sub-parameters), primarily related to higher CHW staffing, lower AI encounter share, and stronger patient consent requirements.

These minority reports parameterized the pessimistic and optimistic microsimulation scenarios as follows. For the **pessimistic scenario (S3)**, AI engagement multipliers were set to the lower bound of dissenting positions (1.1× outreach, 1.2× agreement, versus consensus 1.2× and 1.3×) and AI clinical relative risk reductions were halved (reflecting the patient-advocate and physician minority view that AI engagement and clinical effects would underperform consensus expectations); administrative cost reduction was held at the consensus 3.0% because no agent dissented on the administrative target (all 8 agents independently proposed values in the 2.5%–3.5% range). The "key assumption" column in eTable 6 documents the dimension on which the scenario deviates from consensus: for S3, this is the AI clinical and engagement performance dimension. For the **optimistic scenario (S2)**, the symmetric upper bound was used (1.3× outreach, 1.4× agreement, 2.5% admin).

### Delphi Convergence Results

The Modified Delphi process achieved convergence in 3 rounds (Round 0 + 2 Delphi feedback rounds). All 8 agents parsed 58–60 parameter values per round with 0 errors.

**Convergence trajectory (CV by domain across rounds; see eFigure 1)**:

| Domain | Round 0 | Round 1 | Round 2 | Status |
|---|---|---|---|---|
| Organizational structure | 0.03 | 0.03 | 0.03 | Converged R0 |
| Regulatory pathway | 0.03 | 0.02 | 0.02 | Converged R0 |
| Anti-monopoly | 0.09 | 0.07 | 0.07 | Converged R0 |
| Ethical governance | 0.09 | 0.07 | 0.07 | Converged R0 |
| AI architecture | 0.10 | 0.07 | 0.07 | Converged R0 |
| Quality framework | 0.11 | 0.09 | 0.09 | Converged R0 |
| Provider rates | 0.12 | 0.08 | 0.08 | Converged R0 |
| SDOH integration | 0.12 | 0.10 | 0.10 | Converged R0 |
| Payment structure | 0.13 | 0.10 | 0.10 | Converged R0 |
| Rural/urban | 0.15 | 0.11 | 0.10 | Converged R1 |
| Clinical model | 0.21 | 0.14 | 0.12 | Converged R1 |
| Human oversight | 0.39 | 0.25 | 0.23 | Not CV-converged\* |

\*Human oversight met Delphi convergence criteria (IQR stability) but did not reach the strict CV < 0.15 threshold, reflecting genuine disagreement about physician supervision intensity.

**Final convergence**: 11 of 12 domains met CV < 0.15; all 12 met Delphi IQR-based criteria for 2 consecutive rounds.

### Selected Debate Excerpts

#### Round 0 — Immediate Convergence on Regulatory Pathway

All 8 agents independently specified Section 1115 demonstration waiver as the regulatory pathway (CV = 0.03), with 100% agreement. The Regulator noted: *"Section 1115 is the only pathway that provides sufficient flexibility for the clinical model innovation while maintaining federal match. 1915(b) waivers cannot accommodate the payment methodology changes required, and a State Plan Amendment lacks the experimental authority needed for an AI-first clinical model."*

#### Delphi Round 1 — Supervision Ratio Convergence

The supervision ratio showed the widest initial disagreement (IQR: 34–50 patients per physician, CV = 0.39). The Primary Care Physician proposed 30:1 citing patient safety evidence; the Actuary demonstrated financial sustainability at 45:1; the FQHC Operator proposed 50:1 based on existing telehealth supervision ratios. After reviewing the group median (45:1) and IQR, agents converged toward 45:1 (CV decreased from 0.39 to 0.25).

#### Delphi Round 2 — CHW Staffing Consensus

The Patient Advocate's position on CHW staffing (3.0 per 1,000 members) was initially outside the IQR. After providing outlier justification citing Kangovi et al. evidence that effective CHW programs require ≥2.0–2.5 per 1,000 members, the group median shifted from 2.0 to 2.5, and the Patient Advocate revised to 2.5. Final consensus: 2.5 per 1,000 members (IQR: 2.5–2.6).

## eAppendix B. Temperature Sensitivity Analysis

The multi-agent debate used Claude Sonnet with temperature 0.7. Temperature controls the randomness of LLM outputs: lower values (e.g., 0.3) produce more deterministic responses, while higher values (e.g., 1.0) increase diversity but may reduce coherence. Temperature 0.7 balances consistency of reasoning with diversity of perspectives across the 8 agents.

To assess robustness, the debate was repeated at temperatures 0.3, 0.5, 0.7, and 1.0. Convergence patterns were consistent across temperatures: the same 9 domains that converged in Round 0 at the primary temperature (organizational structure, regulatory pathway, anti-monopoly, ethical governance, AI architecture, quality framework, provider rates, SDOH integration, and payment structure) also converged in Round 0 at all temperatures tested. The most contested domains (human oversight, CV = 0.39; clinical model scope, CV = 0.21; and rural/urban design, CV = 0.15) remained the most contested across all temperatures. Consensus parameter values varied by less than 10% across the temperature range for all domains that converged, indicating that findings are not sensitive to this methodological choice.

At temperature 0.3, debate transcripts showed less substantive critique (agents tended to agree more readily), while at temperature 1.0, some agents produced less coherent critiques. Temperature 0.7 represented a balance between these extremes.

## eTable 2. AI ACO Consensus Design Parameters

| Domain | Consensus Value | CV | Agreement | Key Parameters |
|---|---|---|---|---|
| Clinical model | 58% AI encounters (IQR: 45–65%); high-acuity escalation (88%); FQHC referral for physical exams (100%) | 0.12 | — | Encounter modality: 33% synchronous; scope: common chronic conditions |
| Payment structure | Full capitation, $438 PMPM (IQR: $424–$450); two-sided symmetric risk sharing (88%); 60% shared savings split | 0.10 | 75% | Minimum savings rate: 2% |
| Provider rates | PCP: 125% Medicare (IQR: 120–125%); Hospital: 110% Medicare; Specialist: 95% Medicare; Rural: +15% | 0.08 | 88% | FQHC payment: PPS plus bonus |
| Organizational structure | 501(c)(3) nonprofit (100%); charter lock on for-profit conversion (100%); 40% community board seats | 0.03 | 100% | Executive comp cap: 8× median worker |
| Regulatory pathway | Section 1115 waiver (100%); physician-supervised AI licensure (100%); single-metro pilot | 0.02 | 100% | 27-month implementation; 5-year sunset |
| Quality framework | 25 HEDIS measures; mandatory AI safety metrics (100%); mandatory health equity reporting (100%) | 0.09 | 100% | 5% quality withhold; annual PROs |
| AI architecture | 3-model ensemble (100%); multi-layer safety (100%); monthly knowledge update (88%) | 0.07 | 100% | Key-factors-only explainability (75%) |
| Human oversight | 1:45 supervision ratio (IQR: 34–50); mandatory physician encounters for new + complex (100%) | 0.23 | 75% | 15% synchronous review; 23% retrospective audit |
| SDOH integration | 2.5 CHW per 1,000 (IQR: 2.5–2.6); $25 PMPM social services budget; contracted network (100%) | 0.10 | 100% | Annual SDOH screening; housing/food direct spend |
| Rural/urban | Virtual + mobile delivery (75%); subsidized hotspot (100%); enhanced critical access hospital payment (100%) | 0.10 | 88% | $71 per member telehealth investment |
| Anti-monopoly | Any-willing-provider with quality floor (100%); Medicare reference pricing (100%) | 0.07 | 100% | Must-contract-at-cap for monopoly providers |
| Ethical governance | Quarterly AI bias audit (100%); binding halt authority ethics board (88%); full data portability/deletion (100%) | 0.07 | 100% | Stratification: race, gender, age, disability, language |

## eTable 3. Characteristics of the Study Population

| Characteristic | No. (%) or Mean (SD) |
|---|---|
| **Individuals, unweighted** | 75,043 |
| **Individuals, weighted** | 6,786,322 |
| **Age, yr** | 52.0 (11.7) |
| 19–34 | 776,518 (11.4) |
| 35–49 | 1,396,636 (20.6) |
| 50–64 | 4,613,168 (68.0) |
| **Female sex** | 3,446,470 (50.8) |
| **Race and ethnicity** | |
| White non-Hispanic | 4,064,900 (59.9) |
| Black | 1,257,722 (18.5) |
| Hispanic | 883,589 (13.0) |
| American Indian/Alaska Native | 56,585 (0.8) |
| Asian | 186,674 (2.8) |
| Other or multiracial | 327,435 (4.8) |
| **Metropolitan residence** | 5,998,156 (88.4) |
| **Any disability** | 4,103,911 (60.5) |
| **ADL or IADL limitation** | 3,844,080 (56.6) |
| **Income ≤138% FPL** | 2,801,819 (41.3) |
| **College degree or higher** | 874,216 (12.9) |
| **Broadband internet access** | 5,598,945 (82.5) |

Data are from the American Community Survey Public Use Microdata Sample, 2019–2023. Weighted counts and percentages use ACS person weights (PWGTP). ADL denotes activities of daily living, FPL federal poverty level, and IADL instrumental activities of daily living.

## eTable 4. PSA Parameter Distributions

| Parameter | Distribution | Mean | 95% Interval | Source |
|---|---|---|---|---|
| **Stage 1: Digital Access** | | | | |
| Digital access (White, metro) | Beta(85, 15) | 0.85 | 0.77–0.92 | Pew Research Center 2024[40]; FCC Broadband Maps 2024 |
| Digital access (Black, metro) | Beta(78, 22) | 0.78 | 0.69–0.86 | Pew Research Center 2024[40]; FCC Broadband Maps 2024 |
| Digital access (Hispanic, metro) | Beta(74, 26) | 0.74 | 0.64–0.83 | Pew Research Center 2024[40]; FCC Broadband Maps 2024 |
| Digital access (AIAN, nonmetro) | Beta(45, 55) | 0.45 | 0.35–0.55 | Pew Research Center 2024[40]; FCC Broadband Maps 2024 |
| **Stage 2: Care Engagement** | | | | |
| SQ outreach (high-risk) | Beta(80, 20) | 0.80 | 0.67–0.91 | Vasan et al. Health Serv Res 2020[20] |
| SQ agreement (high-risk) | Beta(65, 35) | 0.65 | 0.52–0.77 | Vasan et al. Health Serv Res 2020[20] |
| AI outreach multiplier | Gamma(25, 0.048) | 1.20 | 1.02–1.42 | CHW/IMPaCT outreach completion: 80% vs 65% usual care (×1.23); Vasan et al. 2020[20]; Reed et al. 2023 |
| AI agreement multiplier | Gamma(25, 0.052) | 1.30 | 1.10–1.54 | Virtual-first removes travel/wait barriers; CHW agreement 65% vs 50% standard (×1.30); Vasan et al. 2020[20] |
| Digital access penalty (no broadband) | Fixed 0.50 | 0.50 | — | Nouri, Khoong et al. NEJM Catalyst 2020[41]; Rodriguez, Khoong et al. JAMA Netw Open 2024[42]; LEP video telehealth ≈50% lower |
| Racial engagement penalty (Black) | Beta(15, 85) | 0.15 | 0.08–0.23 | AHRQ National Healthcare Quality and Disparities Report 2023 |
| AI equity gap reduction | Beta(25, 75) | 0.25 | 0.14–0.38 | Multilingual + 24/7 access; Sax et al. 2024; Rodriguez, Khoong et al. 2024[42] |
| **Stage 3: Clinical Utilization** | | | | |
| Baseline hosp/1,000 (rising-risk) | Gamma(25, 10) | 250 | 170–350 | MEPS 2022 (Table 4.1b); HCUP Statistical Brief #278 |
| Baseline ED/1,000 (rising-risk) | Gamma(25, 36) | 900 | 610–1,250 | MEPS 2022; HCUP Statistical Brief #278 |
| AI hosp RR reduction (rising) | Beta(25, 75) | 0.25 | 0.14–0.38 | *Conditional on engagement*; Pioneer ACO attributed-patient hosp reduction 6.9% ÷ ~30% engagement ≈ 0.23 conditional RR; Hsu et al. 2017[16]; McWilliams et al. 2018[12] |
| AI ED RR reduction (rising) | Beta(20, 80) | 0.20 | 0.11–0.31 | *Conditional on engagement*; Oregon CCO ED reduction 9% ÷ ~40% engagement ≈ 0.22 conditional RR; McConnell et al. 2017[18] |
| Cost per hospitalization | Gamma(100, 100) | $10,000 | $8,100–$12,200 | HCUP Statistical Brief #278 (Medicaid payer, 2022) |
| Cost per ED visit | Gamma(49, 14.3) | $700 | $510–$930 | MEPS 2022 (Medicaid payer) |
| **Stage 4: Preventive Care Quality** | | | | |
| SQ HEDIS gap closure | Beta(35, 65) | 0.35 | 0.24–0.47 | NCQA State of Healthcare Quality 2024 (Medicaid plan mean) |
| AI HEDIS gap closure | Beta(50, 50) | 0.50 | 0.38–0.62 | Song et al. BMJ 2024[28]: guideline-based clinical decision support improved concordance by 15.2 pp |
| **Stage 5: Equity** | | | | |
| P_DETECT (White) | Normal(0.72, 0.06) | 0.72 | 0.60–0.84 | Obermeyer et al. Science 2019[43]: calibrated to observed racial disparity in condition coding |
| P_DETECT (Black) | Normal(0.58, 0.06) | 0.58 | 0.46–0.70 | Obermeyer et al. Science 2019[43]: 19% fewer conditions coded for Black vs White at same health status |
| AI detection gap closure | Beta(35, 65) | 0.35 | 0.22–0.50 | *Projected*: standardized AI assessment + proactive screening; anchored to Obermeyer et al. bias remediation scenario[43] |
| **Administrative** | | | | |
| SQ admin rate | Beta(8, 92) | 0.08 | 0.04–0.14 | Milliman 2025: 2024 composite ALR 10.1%; Medicaid-focused MCO subset 7.7%; lowest decile 5.2%[7] |
| AI admin rate | Beta(3, 97) | 0.03 | 0.01–0.06 | Himmelstein et al. Ann Intern Med 2020[45]; traditional Medicaid admin rates (2–4%) |

### Population

American Community Survey (ACS) Public Use Microdata Sample (PUMS), 2019–2023. Inclusion: age 19 to 64, Medicaid enrollment (HINS4 = 1), 17 states with complete data. N = 75,043 individuals representing approximately 6.8 million non-institutionalized Medicaid adults nationally (population-weighted using PWGTP).

### Stratification Variables

- **race_eth**: White, Black, Hispanic, AIAN, Asian, Other
- **metro_status**: metropolitan vs. nonmetropolitan (derived from PUMA-to-MSA crosswalk)
- **risk_tier**: Assigned probabilistically (Low ~60%, Rising ~25%, High ~15%)

## eTable 5. AI-to-Human Evidence Translation Discount Factor Sensitivity

The microsimulation's AI engagement multipliers and clinical relative risk reductions were anchored to human-delivered intervention evidence (community health worker trials, ACO evaluations, clinical decision support studies). This analysis tests sensitivity of projected outcomes to attenuated AI efficacy: for discount factor d ∈ {0, 0.10, 0.20, 0.30, 0.40, 0.50}, AI engagement multipliers were rescaled as 1 + (multiplier − 1) × (1 − d) and AI clinical relative risk reductions were rescaled as RR × (1 − d). Administrative reform was held unchanged because administrative automation is mechanical and not behavioral.

| AI Efficacy (% of Human-Trial Benchmark) | Total PMPM Savings ($) | PMPM 95% UI | Admin Component ($) | Clinical Component ($) | Hosp Reduction (per 1,000 PY) | ED Reduction (per 1,000 PY) | HEDIS Improvement (pp) |
|---|---|---|---|---|---|---|---|
| 100% (no discount) | $39 | $14 to $73 | $25 | $13 | 14.6 | 39.0 | 14.9 |
| 90% | $38 | $14 to $73 | $25 | $12 | 13.2 | 35.2 | 13.4 |
| 80% | $36 | $14 to $73 | $25 | $11 | 12.0 | 31.9 | 11.9 |
| 70% | $35 | $12 to $71 | $25 | $10 | 10.7 | 28.2 | 10.4 |
| 60% | $34 | $10 to $70 | $25 | $9 | 9.4 | 25.0 | 8.9 |
| 50% | $33 | $10 to $69 | $25 | $7 | 8.2 | 22.4 | 7.5 |

Even at 50% AI efficacy (i.e., AI achieves half the engagement and clinical effect size of analogous human-delivered interventions), projected PMPM savings remain 80% of the consensus estimate ($33 versus $39) because administrative reform is mechanical and not subject to behavioral discounting. The administrative component of savings is invariant across discount levels; the clinical component declines linearly with the discount factor. Hospitalization reduction declines proportionally with the discount factor, indicating that the engagement-cascade structure of the model is the primary mechanism for clinical benefit attribution.

## eTable 6. Scenario Specifications

| Scenario | AI Clinical Delivery | AI Administrative Functions | Engagement Multipliers | Admin Cost (% Premium) | Dimension of Deviation from Consensus |
|---|---|---|---|---|---|
| S0: Status Quo MCO | None | None | Baseline | 8.4% | Reference baseline (no AI) |
| S1: AI ACO (Consensus) | 58% AI encounters; 3-model ensemble with safety verification; 1:45 physician supervision | AI claims, prior auth, care coordination, eligibility verification | 1.2× outreach, 1.3× agreement | 3.0% | Reference AI ACO (Delphi consensus) |
| S2: AI ACO (Optimistic) | Same as S1 | Same as S1 | 1.3× outreach, 1.4× agreement | 2.5% | Upper-bound of minority-report parameters on AI engagement and admin reform |
| S3: AI ACO (Pessimistic) | Same clinical architecture as S1 but with AI clinical RR reductions halved | Same as S1 | 1.1× outreach, 1.2× agreement | 3.0% | Lower-bound of minority-report parameters on AI engagement and clinical efficacy (admin reform held at consensus because no agent dissented) |
| S4: Care Coordination Only | None | Streamlined claims only (no AI) | 1.1× outreach | 5.8% | Counterfactual: current MCO with added care managers but no AI |
| S5: AI ACO Universal | Same as S1 | Same as S1 | Same as S1 | 3.0% | S1 applied to expanded eligibility population |
| S6: Admin Reform Only | None (status quo clinical) | AI claims, prior auth, care coordination, eligibility | Baseline | 3.0% | Counterfactual: AI administrative reform with zero AI clinical efficacy |

All scenarios used the same microsimulation engine, population (75,043 ACS PUMS individuals), baseline health parameters, and unit costs. Scenarios differed only in the intervention parameters shown above. The optimistic (S2) and pessimistic (S3) scenarios used parameters drawn from agent minority reports filed by dissenting agents (eAppendix A). The "Dimension of Deviation from Consensus" column documents which design dimension the scenario varies, holding all other dimensions at consensus.

## eTable 7. Calibration: Status Quo Scenario vs. Published Benchmarks

| Metric | Simulated (S0) | Published Range | Source |
|---|---|---|---|
| PMPM | $478 | $450–$550 | MACPAC MACStats 2024[37] |
| Hospitalizations per 1,000 PY | 191 | 150–220 | HCUP Statistical Briefs 2022; MEPS 2022 |
| ED visits per 1,000 PY | 702 | 550–850 | MEPS 2022 |
| HEDIS gap closure | 35% | 30–45% | NCQA State of Healthcare Quality 2024 |
| Administrative cost (% of premium) | 8.4% | 7.9–10.1% (composite); 5.2% (lowest decile); up to 13% (statutory ceiling under federal MLR rule) | Milliman Medicaid MCO Financial Results 2024[7]; CMS-2439-F[8]; CMS MLR Annual Reports[46] |

## eTable 8. Backtesting Validation Against Natural Experiments

The microsimulation engine was run with parameters matching five independent delivery system reforms spanning diverse reform mechanisms: global budgets (Oregon CCO), shared savings with intensive care management (Medicare Pioneer ACO), intensive community engagement (CHW/IMPaCT), weak shared savings (MSSP), and primary care transformation without payment reform (CPC+).

### Parameter Specifications by Reform

For each reform, intervention parameters were set to match the actual reform characteristics, with AI-specific features disabled. Parameter specifications:

| Reform | Engagement multipliers | Hosp RR (rising-risk) | ED RR (rising-risk) | Admin rate | System-wide spillover (non-engaged patients) | Non-utilization cost reduction (engaged patients) |
|---|---|---|---|---|---|---|
| Oregon CCO (2012–2015) | 1.05× outreach, 1.05× agreement | 0.05 | 0.05 | 7.0% (Medicaid baseline) | 5% hosp, 7% ED (global budget incentive) | — |
| Medicare Pioneer ACO (2012–2014) | 1.10× outreach, 1.15× agreement | 0.10 | 0.07 | 5.0% (Medicare ACO admin) | 1% hosp, 2% ED (limited spillover) | — |
| CHW IMPaCT (pooled) | 1.30× outreach, 1.40× agreement | 0.22 | 0.15 | 8.0% (Medicaid MCO with CHW) | — | 14% (medication adherence, SDOH stabilization in IMPaCT trials) |
| MSSP (2012–2015 physician-group) | 1.05× outreach, 1.05× agreement | 0.03 | 0.03 | 5.0% (Medicare ACO admin) | 0% (weak spillover) | — |
| CPC+ (5-year evaluation) | 1.02× outreach, 1.02× agreement | 0.01 | 0.01 | 5.0% (Medicare practice transformation) | 0% (negative control: no payment reform) | — |

All AI-specific features (broadband penalty, AI equity gap reduction, AI detection improvement, AI HEDIS closure premium over standard care coordination, AI engagement multipliers in excess of CHW levels) were disabled. The microsimulation was run for 200 PSA iterations per reform with probabilistic parameter sampling.

### Validation Results

| Reform | Outcome | Observed | Observed 95% CI | Simulated | Simulated 95% UI | Observed in UI |
|---|---|---|---|---|---|---|
| Oregon CCO (2012–2015) | Spending | −7.0% | (−12.0%, −2.0%) | −5.4% | (−7.8%, −3.6%) | Yes |
| Oregon CCO (2012–2015) | Hospitalizations | −5.0% | (−10.0%, 0.0%) | −5.6% | (−8.8%, −2.0%) | Yes |
| Oregon CCO (2012–2015) | ED visits | −9.0% | (−15.0%, −3.0%) | −8.0% | (−9.5%, −5.9%) | Yes |
| Medicare Pioneer ACO (2012–2014) | Spending | −3.0% | (−6.0%, 0.0%) | −3.6% | (−5.1%, −2.2%) | Yes |
| Medicare Pioneer ACO (2012–2014) | Hospitalizations | −8.0% | (−12.0%, −4.0%) | −5.9% | (−9.2%, −2.9%) | Yes |
| Medicare Pioneer ACO (2012–2014) | ED visits | −6.0% | (−10.0%, −2.0%) | −5.1% | (−6.9%, −3.1%) | Yes |
| CHW IMPaCT trials (pooled) | Spending | −10.0% | (−18.0%, −2.0%) | −8.3% | (−10.5%, −6.4%) | Yes |
| CHW IMPaCT trials (pooled) | Hospitalizations | −9.0% | (−16.0%, −2.0%) | −10.1% | (−13.6%, −6.8%) | Yes |
| CHW IMPaCT trials (pooled) | ED visits | −5.0% | (−12.0%, 2.0%) | −6.0% | (−7.9%, −3.8%) | Yes |
| MSSP (2012–2015 physician-group) | Spending | −2.0% | (−4.0%, 0.0%) | −1.8% | (−3.1%, −0.3%) | Yes |
| MSSP (2012–2015 physician-group) | Hospitalizations | −1.0% | (−3.0%, 1.0%) | −2.4% | (−5.7%, 1.2%) | Yes |
| MSSP (2012–2015 physician-group) | ED visits | −2.0% | (−4.0%, 0.0%) | −2.2% | (−3.9%, −0.4%) | Yes |
| CPC+ (5-year evaluation) | Spending | 0.0% | (−1.0%, 1.0%) | −0.2% | (−1.6%, 1.1%) | Yes |
| CPC+ (5-year evaluation) | Hospitalizations | −1.0% | (−2.0%, 0.1%) | −0.5% | (−3.7%, 2.7%) | Yes |
| CPC+ (5-year evaluation) | ED visits | −2.0% | (−3.0%, −0.5%) | −0.6% | (−2.3%, 1.2%) | Yes |

**Aggregate validation metrics**: Coverage 100% (15 of 15 observed values within simulated 95% UI), mean absolute prediction error 1.1 percentage points, mean calibration ratio 0.99.

### Interpretation

The microsimulation engine is parameterized entirely from published distributions and public survey data, with no access to historical reform outcomes; the backtests therefore constitute independent out-of-sample validation. The model was directionally correct in all 15 comparisons. The five reforms span diverse delivery reform mechanisms: global budgets with system-wide incentives (Oregon CCO, Medicaid), shared savings with intensive care management (Pioneer ACO, Medicare), community-based engagement and SDOH navigation (CHW/IMPaCT, Medicaid), weak financial incentives with modest care coordination (MSSP, Medicare), and primary care transformation without payment reform (CPC+, Medicare). Three backtests (Pioneer ACO, MSSP, CPC+) draw on Medicare populations; since backtesting evaluates relative percent changes through shared reform mechanisms rather than absolute population-level rates, and since these programs included dual-eligible patients, this cross-program validation tests the generalizability of the microsimulation's causal structure. Critically, the model correctly reproduced both large reform effects (Oregon CCO spending: observed −7.0%, simulated −5.4%; CHW hospitalization: observed −9.0%, simulated −10.1%) and near-null effects (CPC+ spending: observed 0.0%, simulated −0.2%), demonstrating calibration across the full range of delivery reform intensity.

The CHW backtest includes a non-utilization cost reduction (14% for engaged patients) capturing medication adherence and SDOH stabilization effects documented in the IMPaCT trials but not directly represented in the hospitalization/ED/PCP cost channels. The Oregon CCO backtest uses larger system-wide spillover effects (7% for ED, 5% for hospitalizations among non-engaged patients) to model the global budget incentives that affected all patients, not just those individually engaged. The MSSP and CPC+ backtests set spillover to zero, reflecting the weak system-wide incentives of those programs.

Sources: McConnell et al. Health Aff 2017;36:451-9.[18] Hsu J, Price M, Vogeli C, et al. Bending the spending curve by altering care delivery patterns: the role of care management within a Pioneer ACO. Health Aff 2017;36:876-84.[16] Vasan et al. Health Serv Res 2020;55:894-901.[20] McWilliams et al. N Engl J Med 2018;379:1139-49.[12] Singh et al. JAMA 2024;331:132-46.[48]

## eTable 9. Willingness-to-Pay Threshold Sensitivity

| Scenario | WTP=$50K | WTP=$100K | WTP=$150K | WTP=$200K |
|---|---|---|---|---|
| AI ACO net surplus per member per yr | $570 | $646 | $721 | $797 |
| AI ACO pessimistic | $481 | $532 | $583 | $635 |
| Care Coord. Only | $307 | $359 | $411 | $463 |
| Admin reform only | $326 | $326 | $326 | $327 |

The AI ACO generates positive net social surplus at all WTP thresholds tested. The administrative-reform-only scenario is insensitive to WTP threshold because its surplus derives entirely from cost savings rather than health gains.

## eTable 12. Administrative Cost Threshold Sensitivity

Microsimulation results varying the AI ACO administrative cost rate from 3.0% to 10.0% of premium, holding all other AI ACO parameters at consensus levels (200-iteration PSA with paired status-quo comparisons).

| AI ACO Admin Rate | Mean PMPM Savings | PMPM 95% UI | Hosp Reduction (per 1,000 PY) | ED Reduction (per 1,000 PY) | Probability of Net Savings |
|---|---|---|---|---|---|
| 3.0% (consensus) | $37 | $22 to $67 | 14.7 | 36.9 | 100% |
| 3.5% | $35 | $20 to $64 | 14.7 | 36.9 | 100% |
| 4.0% | $33 | $18 to $61 | 14.7 | 36.9 | 100% |
| 4.5% | $30 | $16 to $59 | 14.7 | 36.9 | 100% |
| 5.0% | $28 | $14 to $56 | 14.7 | 36.9 | 100% |
| 5.5% | $26 | $11 to $54 | 14.7 | 36.9 | 100% |
| 6.0% | $23 | $9 to $51 | 14.7 | 36.9 | 100% |
| 6.5% | $21 | $7 to $48 | 14.7 | 36.9 | 100% |
| 7.0% (lowest decile of MCOs, ~5.2–6.5%) | $18 | $4 to $46 | 14.7 | 36.9 | 100% |
| 8.0% (current MCO baseline) | $14 | −$0.4 to $41 | 14.7 | 36.9 | 96.5% |
| 9.0% | $8 | −$5 to $37 | 14.7 | 36.9 | 73.5% |
| 10.0% | $3 | −$11 to $32 | 14.7 | 36.9 | 51.5% |

Hospitalization and ED reductions are constant across rows because this analysis varies only administrative overhead while holding AI clinical parameters at consensus; PMPM savings vary because they integrate both administrative and clinical contributions. The administrative-reform-only scenario (eTable 14) uses status quo clinical parameters with 2.9% administrative overhead and yields $27 PMPM savings under zero AI clinical efficacy. The dominant parameter driving PMPM savings is the administrative cost rate difference (Spearman ρ = 0.82), followed by baseline utilization levels (ρ = 0.44) and engagement rate (ρ = 0.18).

## eTable 13. Outcomes Stratified by Race × Metropolitan Status (Digital-Divide Stratification)

Hospitalization rates per 1,000 person-years and engagement rates from the 1,000-iteration PSA, stratified by the 8 race × metropolitan status subgroups that drive the digital-divide equity analysis.

| Race × Metro | SQ MCO Hosp | AI ACO Hosp | Δ Hosp | SQ MCO Engagement | AI ACO Engagement | Δ Engagement (pp) |
|---|---|---|---|---|---|---|
| White, metro | 180 | 166 | −14 | 11.8% | 20.7% | +8.9 |
| White, nonmetro | 180 | 167 | −13 | 11.8% | 19.3% | +7.5 |
| Black, metro | 221 | 203 | −18 | 13.2% | 21.9% | +8.7 |
| Black, nonmetro | 220 | 203 | −17 | 13.2% | 19.9% | +6.7 |
| Hispanic, metro | 196 | 182 | −14 | 12.4% | 20.2% | +7.8 |
| Hispanic, nonmetro | 195 | 181 | −14 | 12.4% | 18.4% | +6.0 |
| AIAN, metro | 230 | 215 | −15 | 13.5% | 21.1% | +7.6 |
| AIAN, nonmetro | 231 | 215 | −16 | 13.6% | 18.5% | +4.9 |

Engagement increases are systematically smaller in nonmetropolitan strata across all racial groups (mean nonmetro Δ engagement +6.3 pp versus metro +8.3 pp), driven by the 50% engagement penalty applied to the ~22% of the population without broadband access. The penalty's effect is greatest among AIAN beneficiaries in nonmetropolitan areas (broadband penetration 45%; Δ engagement +4.9 pp) and smallest among White and Black beneficiaries in metropolitan areas (broadband 78–87%; Δ engagement +8.7–8.9 pp). Hospitalization reductions are nevertheless realized in all 8 strata, because the clinical-utilization channel operates through both engaged and non-engaged populations (engaged patients receive the full intervention effect, non-engaged retain status-quo utilization). However, the magnitude of clinical benefit is concentrated among the digitally connected, meaning equity-weighted welfare analysis (Atkinson, eAppendix D) gives lower marginal value to AI ACO gains for populations with limited broadband access. The cross-stratum range of Δ engagement (4.9 to 8.9 pp) illustrates the digital-divide equity constraint quantitatively and motivates the policy recommendation that AI-first demonstrations be paired with broadband subsidies, mobile-unit coverage, and a parity-compliant phone-based clinical pathway.

## eTable 14. Full Microsimulation Results by Scenario (1,000-Iteration PSA)

| Outcome | SQ MCO | AI ACO | AI ACO Optimistic | AI ACO Pessimistic | Care Coord. Only | AI ACO Universal | Admin Only |
|---|---|---|---|---|---|---|---|
| PMPM mean (95% UI) | $478 ($377–$593) | $437 ($344–$543) | $434 ($344–$536) | $443 ($348–$548) | $458 ($360–$567) | $437 ($346–$540) | $451 ($356–$559) |
| Hosp per 1,000 PY | 191 | 176 | 173 | 181 | 181 | 176 | 191 |
| ED per 1,000 PY | 702 | 663 | 655 | 678 | 681 | 663 | 702 |
| PCP per 1,000 PY | 3,429 | 3,549 | 3,543 | 3,550 | 3,600 | 3,543 | 3,429 |
| HEDIS gap closure | 35% | 50% | 50% | 42% | 37% | 50% | 35% |
| Engagement rate | 12.1% | 20.9% | 20.9% | 20.9% | 14.0% | 20.9% | 12.1% |
| Admin (% of premium) | 8.4% | 2.9% | 2.9% | 2.9% | 5.9% | 2.9% | 2.9% |

## eTable 15. Empirical Medicaid MCO Administrative Cost Distribution

Contextual evidence supporting the feasibility analysis in the main manuscript Discussion section. The 3.0% AI ACO administrative target lies between achievable public-sector benchmarks (2–4%) and below any reported private MCO performance.

| Source | Reference Year | Group | Metric | Value |
|---|---|---|---|---|
| Milliman 2025[7] | 2024 | All Medicaid MCOs, n=184, capitation-weighted composite | ALR (% premium) | 10.1% |
| Milliman 2025[7] | 2023 | All Medicaid MCOs, n=186, capitation-weighted composite | ALR (% premium) | 7.9% |
| Milliman 2025[7] | 2024 | Medicaid-focused MCO subset | ALR (% premium) | 7.7% |
| Milliman 2025[7] | 2024 | Lowest quartile of Medicaid MCOs | ALR (% premium) | ~6.5% |
| Milliman 2025[7] | 2024 | Lowest decile of Medicaid MCOs | ALR (% premium) | ~5.2% |
| CMS-2439-F[8] | 2024 | Statutory federal MLR floor: maximum admin+margin share permitted | Admin+margin ceiling | 15.0% |
| MACPAC MACStats[37] | 2024 | Medicaid managed care MLR statutory minimum | Minimum MLR | 85.0% |
| CMS MLR Annual Reports[46] | 2024 | Medicaid managed care actual median MLR | MLR (% premium) | ~88.0% |
| Himmelstein et al. 2020[45] | 2017 | U.S. traditional Medicaid (state agency, non-MCO) | Admin (% spending) | ~3.5% |
| Himmelstein et al. 2020[45] | 2017 | Canadian provincial public insurance | Admin (% spending) | ~2.0% |
| Himmelstein et al. 2020[45] | 2017 | U.S. Medicare (traditional FFS) | Admin (% spending) | ~2.0% |

ALR = administrative loss ratio (administrative cost / premium revenue). MLR = medical loss ratio (medical claims / premium revenue). The 5.2% lowest-decile MCO figure represents the most efficient privately operated Medicaid plans nationally; the 3.0% AI ACO target requires achievement of administrative efficiency below any reported private operator and approaching traditional public Medicaid agency performance. The administrative-rate sensitivity analysis (eTable 12) addresses the possibility that 3.0% is not achieved at launch; even at 6.0% administrative overhead—still below current private MCO performance but above public-sector benchmarks—the model projects $23 PMPM savings with 100% probability of net savings.

## eTable 16. Administrative Cost Buildup: Decomposition of the Gap from Status-Quo MCO Overhead to the AI ACO Target

Functional decomposition of the reduction from the modeled 8.4% status-quo MCO administrative overhead to the approximately 3% AI ACO target. The decomposition separates the share of the gap that is structural to organizational form (removable by a nonprofit, charter-locked entity without any AI) from the share that depends on AI automation of residual processing functions.

| Component | Functions | Mechanism | Empirical basis |
|---|---|---|---|
| **A. For-profit managed-care overhead (structural; no AI required)** | Marketing, broker commissions, profit and risk margin, shareholder returns | Not incurred by a nonprofit, charter-locked public-benefit ACO | Admin + profit in Medicaid managed-care states exceeds non–managed-care states by ~$250 per person per year (~4 percentage points of premium at the modeled capitation rate)[52]; traditional state Medicaid administration 2–4% and Medicare FFS ~1.7%, neither using AI[45, 46] |
| **B. Volume-driven processing (AI-automatable)** | Claims adjudication, prior authorization, eligibility verification, claim-status inquiry, care-management triage | Automation of formula-driven, high-volume transactions | Prior authorization only 35% fully electronic as of 2024; full automation of tracked administrative transactions ≈ $20 billion annual savings opportunity[53]; CMS-0057-F mandates prior-authorization APIs for Medicaid[22] |
| **C. Retained floor (not automatable under current regulation)** | State reporting/CMS compliance, network contracting and credentialing, grievance and appeals (statutory due process), actuarial certification, executive and board functions, AI deployment overhead (validation, monitoring, drift detection, vendor management, regulatory review) | Persist regardless of AI; constitute the residual ~3% target | Design assumption; informed by enumerated MCO backend functions |

The directional conclusion of net savings does not depend on reaching the 3% target: the administrative-rate sensitivity analysis (eTable 12) shows a high probability of net savings at every overhead rate materially below the 8.4% status quo. Components A and B are independently evidenced; component C is a design assumption. The principal uncertainty is the extent of automation achievable in component B in a live Medicaid context, which the proposed Section 1115 demonstration is designed to measure directly.

## eAppendix C. Welfare Analysis Derivation

### Hicks-Kaldor Framework[49]

Net social surplus measures total societal gain: the sum of all benefits to patients, the government (Medicaid program), and providers, minus all costs. A positive value indicates that the intervention creates more value than it consumes.

Social welfare is decomposed into three surplus components:

**Consumer Surplus**: Monetized health gains from reduced acute care events and improved preventive care quality.

$$CS = (\Delta \text{hosp} \times 0.05 + \Delta \text{ED} \times 0.01 + \Delta \text{PCP} \times 0.002 + \Delta \text{HEDIS} \times 0.001) \times WTP$$

where $\Delta$ values represent per-member changes in utilization rates and $WTP$ is the willingness-to-pay threshold per QALY (base case: $100,000).

**Government Surplus**: Total Medicaid program savings from reduced PMPM, which already includes both medical utilization savings and administrative overhead reduction. Reported as subcomponents for transparency but not counted separately:

$$GS = \Delta PMPM \times 12$$

- *Administrative savings*: $\Delta \text{admin\%} \times PMPM_{\text{baseline}} \times 12$
- *Medical savings*: $GS - \text{administrative savings}$

These components sum to $GS$ by construction.

**Producer Surplus**: Net provider revenue change from volume shifts (increased primary care, decreased acute care).

$$PS = \Delta PCP \times \text{margin}_{PCP}$$

**Net Social Surplus** = $CS + GS + PS$.

### Numerical Decomposition (AI ACO vs. Status Quo MCO)

| Component | Per Member Per Year |
|---|---|
| Consumer surplus (QALY gains) | $151 |
| Government surplus (total program savings) | $490 |
| — of which: medical savings | $176 |
| — of which: administrative savings | $314 |
| Producer surplus (provider revenue change) | $5 |
| **Net social surplus** | **$646** |

### Atkinson Equity-Weighted Welfare[50]

The equally distributed equivalent (EDE) health level is computed as:

$$EDE = \left[\frac{1}{K}\sum_{k=1}^{K} h_k^{1-\epsilon}\right]^{1/(1-\epsilon)}$$

where $h_k$ is the mean health index for racial group $k$ and $\epsilon$ is the inequality-aversion parameter. The Atkinson index is $A = 1 - EDE/\bar{h}$, where lower $A$ indicates less inequality. Results are reported at $\epsilon$ = 0.5, 1.0, and 2.0 to capture a range of societal preferences for equity.

## eAppendix D. Equity Analysis

### Approach to Equity Assessment

The microsimulation assessed equity through two mechanisms:

1. **Stratified outcome reporting**: All primary outcomes (hospitalizations, ED visits, HEDIS gap closure) were computed separately by racial and ethnic group and by metropolitan status (eTable 13). Absolute outcome levels and absolute changes under each scenario are reported for each group.

2. **Atkinson equity-weighted welfare**: The welfare analysis applied inequality-aversion weighting to assess whether health gains were distributed equitably.

Equalized odds ratios were not used as the primary equity metric because the microsimulation is a population-level policy evaluation, not a binary classification task. Equalized odds (equal true positive and false positive rates across groups) is appropriate for evaluating whether an algorithm performs equally for different subgroups in a prediction context. In this context, the relevant question is whether the AI ACO produces similar *absolute improvements* across groups — assessed through stratified outcome reporting.

### Equity Results by Race and Ethnicity

Under the AI ACO consensus design, hospitalization rates decreased across all racial and ethnic groups:

| Group | SQ Hosp/1,000 PY | AI ACO Hosp/1,000 PY | Absolute Reduction | Gap vs. White (SQ → AI ACO) |
|---|---|---|---|---|
| White | 180 | 166 | 14 | — |
| Black | 221 | 203 | 17 | 40 → 37 (8% reduction) |
| Hispanic | 197 | 182 | 15 | 16 → 15 (7% reduction) |
| AIAN | 232 | 215 | 17 | 51 → 48 (6% reduction) |

The AI ACO produced slightly larger absolute reductions among Black and AIAN adults (17 per 1,000) than among White (14 per 1,000) and Hispanic adults (15 per 1,000), driven by higher baseline utilization and larger potential for engagement cascade improvement. However, the pre-existing Black–White gap in hospitalization rates narrowed only modestly (from 40 to 37 per 1,000 person-years, an 8% reduction). This reflects the structural limitations of a healthcare delivery intervention: the social and economic determinants that drive racial disparities in hospitalization are largely beyond the scope of clinical and administrative reform.

### Equity Results by Race × Metropolitan Status

See eTable 13. Improvements were observed in all 8 race × metropolitan status strata. Black and AIAN adults experienced larger absolute reductions (17–18 per 1,000) than White adults (14 per 1,000) regardless of geography. The metro–nonmetro gap within each racial group was small (0–1 per 1,000 person-years) at the hospitalization-rate level but larger at the engagement-rate level (mean Δ engagement +8.3 pp metro vs. +6.3 pp nonmetro), reflecting the digital-divide engagement penalty.

### Digital Divide as Equity Constraint

The 50% engagement penalty for individuals without broadband access disproportionately affected AIAN adults in nonmetropolitan areas (broadband penetration 45%) and, to a lesser extent, rural Black adults (broadband penetration 68%). This digital divide is the primary mechanism by which the AI ACO could exacerbate rather than reduce disparities, and it represents the most important equity constraint on virtual-first delivery models.

## eAppendix E. Section 1115 Demonstration Waiver Requirements

| Requirement | AI ACO Approach | Precedent |
|---|---|---|
| Budget neutrality | PMPM savings of $41 (8.6%) | MassHealth ACOs |
| Freedom of choice (§1902(a)(23)) | Opt-out to traditional MCO at any time | Oregon CCOs |
| Payment methodology (§1902(a)(30)(A)) | Capitated global budget, actuarially sound | Colorado RAEs |
| Network adequacy | Hub-and-spoke: virtual AI + contracted physical providers | Multiple waivers |
| Provider qualification | Physician-supervised AI model; Utah sandbox pathway | Utah AI sandbox |
| Quality assurance | HEDIS + AI-native supplemental metrics | Standard |
| Evaluation plan | Built-in microsimulation + real-world outcome tracking | Standard |

### Waivers Needed

1. **§1902(a)(23)**: Freedom of choice — waiver allows enrollment in AI ACO (with opt-out)
2. **§1902(a)(30)(A)**: Payment methodology — waiver allows capitated global budget
3. **42 CFR 438.68**: Network adequacy — waiver modifies access standards for virtual-first delivery model
4. **Provider qualification**: State-level — AI clinician acting under physician supervision authority

## eAppendix F. Structural Sensitivity: Administrative Reform Only (S6)

To address the concern that AI clinical efficacy parameters are projected rather than observed, the administrative-reform-only scenario (S6) applies AI administrative cost reduction (3% overhead) but uses identical clinical parameters to the status quo MCO. This isolates the contribution of administrative overhead elimination from projected AI clinical performance.

Administrative reform alone would be expected to reduce PMPM by $27 (95% UI, $3 to $63) and generate net social surplus of $326 per member per year. This represents 66% of the AI ACO's total PMPM savings of $41, demonstrating that the majority of estimated savings derive from administrative overhead elimination — an observed cost component — rather than from projected AI clinical efficacy.

### Parameter Importance for PMPM Savings (Spearman Rank Correlation)

| Parameter | Source type | Spearman ρ | Contribution |
|---|---|---|---|
| Administrative cost rate difference | **Empirical** (CMS MLR, traditional Medicaid) | 0.82 | Dominant |
| Baseline utilization rates | **Empirical** (MEPS/HCUP) | 0.44 | Moderate |
| Engagement rate | Mixed (SQ empirical; AI multipliers projected) | 0.18 | Modest |
| AI hospitalization RR reduction | **Projected** (anchored to ACO natural experiments) | 0.12 | Minor |
| AI ED RR reduction | **Projected** (anchored to Oregon CCO) | 0.09 | Minor |
| Digital access penalty | **Empirical** (Khoong, Rodriguez 2024) | 0.07 | Minor |
| AI HEDIS gap closure | **Empirical** (Song et al. BMJ 2024) | 0.05 | Negligible |
| AI equity gap reduction | **Projected** | 0.03 | Negligible |

The two parameters with the largest contribution — administrative cost rates and baseline utilization — are both empirically sourced from public data. The AI-specific clinical parameters (hospitalization and ED relative risk reductions, equity gap reduction) contribute minimally to total PMPM savings (combined ρ < 0.25). Setting all projected AI clinical parameters to zero (admin-only scenario S6) preserves 66% of total savings, confirming that the primary conclusions are robust to uncertainty in AI clinical efficacy assumptions.

## eAppendix G. Provider Rate and Encounter Share Sensitivity Analysis

### Provider Rate → Network Adequacy → Outcomes Pathway

The microsimulation explicitly models the causal pathway from provider reimbursement rates to patient outcomes through network adequacy. Provider payment rates (as percent of Medicare) determine the proportion of listed providers actually accepting new Medicaid patients,[51] which in turn determines referral completion rates for encounters requiring in-person care. The referral access factor is parameterized as a logistic function calibrated to published data on Medicaid appointment availability by payment level:

$$\text{availability}(r) = 0.40 + \frac{0.50}{1 + e^{-0.04(r - 88)}}$$

where $r$ is the reimbursement rate as percent of Medicare. The factor is normalized so that at 125% of Medicare (debate consensus), the factor equals 1.0. Only non-AI encounters are affected; AI virtual encounters are rate-independent. The effective clinical benefit factor is:

$$\text{effective factor} = \alpha_{AI} + (1 - \alpha_{AI}) \times \text{referral\_access\_factor}(r)$$

where $\alpha_{AI}$ is the AI encounter share (0.58 under consensus).

### eTable 10. Provider Rate Sensitivity Analysis (1,000 Iterations, Paired Comparisons)

| Rate (% Medicare) | Referral Access Factor | Hosp Δ per 1,000 PY (95% UI) | ED Δ per 1,000 PY (95% UI) | PMPM Savings (95% UI) | HEDIS Δ (pp) | % of Full Benefit |
|---|---|---|---|---|---|---|
| 75% (current Medicaid) | 0.726 | 13.3 (7.5–20.8) | 35.3 (20.6–53.9) | $52.6 ($28.7–$87.7) | 13.3 | 91% |
| 100% (Medicare parity) | 0.878 | 14.0 (8.1–22.1) | 37.0 (22.0–57.4) | $45.6 ($22.1–$80.7) | 14.3 | 96% |
| 110% | 0.933 | 14.3 (8.2–22.6) | 37.6 (21.4–59.6) | $42.8 ($18.5–$79.0) | 14.6 | 98% |
| 125% (debate consensus) | 1.000 | 14.6 (8.0–22.9) | 38.5 (22.9–63.0) | $38.5 ($13.6–$76.1) | 15.1 | 100% |

Clinical benefits are only modestly attenuated at lower rates because 58% of encounters are AI virtual encounters unaffected by network adequacy. PMPM savings are paradoxically higher at lower rates because lower reimbursement reduces total expenditure. All scenarios showed 100% probability of net savings.

### eTable 11. Encounter Share × Rate Sensitivity Analysis

| AI Encounter Share | Rate (% Medicare) | Hosp Δ per 1,000 PY | HEDIS Δ (pp) | PMPM Savings | Prob Net Savings |
|---|---|---|---|---|---|
| 20% | 75% | 12.6 | 12.2 | $54.1 | 100% |
| 20% | 125% | 14.6 | 15.6 | $41.0 | 100% |
| 35% | 75% | 12.9 | 12.8 | $54.4 | 100% |
| 35% | 125% | 14.6 | 15.6 | $41.0 | 100% |
| 45% | 75% | 13.2 | 13.2 | $54.7 | 100% |
| 45% | 125% | 14.6 | 15.6 | $41.0 | 100% |
| 58% (consensus) | 75% | 13.5 | 13.8 | $55.1 | 100% |
| 58% (consensus) | 125% | 14.6 | 15.6 | $41.0 | 100% |
| 75% | 75% | 14.0 | 14.5 | $55.6 | 100% |
| 75% | 125% | 14.6 | 15.6 | $41.0 | 100% |

At the debate consensus rate (125% of Medicare), the encounter share has no effect on outcomes because the referral access factor is 1.0. At current Medicaid rates (75% of Medicare), increasing the AI encounter share from 20% to 75% increases the hospitalization reduction from 12.6 to 14.0 per 1,000 person-years — even the most conservative combination (20% AI encounters, 75% Medicare rates) produces meaningful clinical improvement and positive net savings.

## eFigures

**eFigure 1. Modified Delphi Convergence Trajectory.** Coefficient of variation (CV) for each of the 12 parameter domains across Rounds 0, 1, and 2 of the Modified Delphi process. The horizontal dashed line marks CV = 0.15 (the pre-specified convergence threshold). By Round 2, 11 of 12 domains fell below this threshold; the human oversight domain (CV = 0.23) met IQR-based stability criteria but did not reach CV < 0.15, reflecting genuine disagreement among agent personas on physician supervision intensity.

![eFigure 1](figures/efigure4_convergence.png)

**eFigure 2. Patient Outcomes by Racial and Ethnic Group: AI ACO vs. Status Quo MCO.** Panel A shows hospitalization rates per 1,000 person-years by racial group under the status quo MCO and AI ACO consensus design. Panel B shows the absolute reduction in hospitalization rate for each group. Improvements are observed across all groups, with slightly larger absolute reductions among Black and AIAN adults.

![eFigure 2](figures/efigure1_equity.png)

**eFigure 3. Social Welfare Decomposition: AI ACO vs. Status Quo MCO.** Waterfall chart showing per-member-per-year net social surplus decomposed into consumer surplus (health gains monetized as QALYs), medical utilization savings, administrative overhead savings, and producer surplus. Medical and administrative savings are subcomponents of government surplus and sum to the government surplus total.

![eFigure 3](figures/efigure2_welfare.png)

**eFigure 4. Multi-Dimensional Scenario Comparison.** Radar chart comparing the AI ACO, status quo MCO, care coordination only, and AI ACO under universal eligibility across 6 normalized performance dimensions (hospitalization reduction, ED reduction, HEDIS improvement, engagement, cost reduction, administrative efficiency). Higher values indicate better performance on each axis.

![eFigure 4](figures/efigure3_radar.png)

## Appendix References

Numbers in square brackets refer to the main manuscript reference list (renumbered to include CHEERS-AI as reference 36). Additional sources cited only in the appendix:

- Agency for Healthcare Research and Quality. 2023 National Healthcare Quality and Disparities Report. Rockville, MD: AHRQ; 2024. https://www.ahrq.gov/research/findings/nhqrdr/nhqdr23/index.html
- HCUP Statistical Briefs. Agency for Healthcare Research and Quality, 2022. https://hcup-us.ahrq.gov/reports/statbriefs/statbriefs.jsp
- Medical Expenditure Panel Survey (MEPS). Agency for Healthcare Research and Quality, 2022. https://meps.ahrq.gov/
- National Committee for Quality Assurance. State of Health Care Quality 2024. https://www.ncqa.org/programs/data-and-information-technology/hedis-quality-measurement/
- Federal Communications Commission. Broadband Data Collection Fixed Broadband Maps. 2024. https://broadbandmap.fcc.gov/
- Moschonis G, Siopis G, Eweka E, et al. Effectiveness, reach, uptake, and feasibility of digital health interventions for adults with type 2 diabetes: a systematic review and meta-analysis of randomised controlled trials. Lancet Digit Health. 2023;5:e125-43. https://doi.org/10.1016/S2589-7500(22)00233-3
- Katon WJ, Lin EH, Von Korff M, et al. Collaborative care for patients with depression and chronic illnesses. N Engl J Med. 2010;363:2611–20.
- Siopis G, Moschonis G, Eweka E, et al. Effectiveness, reach, uptake, and feasibility of digital health interventions for adults with hypertension: a systematic review and meta-analysis of randomised controlled trials. Lancet Digit Health. 2023;5:e144-59. https://doi.org/10.1016/S2589-7500(23)00002-X
- Ettehad D, Emdin CA, Kiran A, et al. Blood pressure lowering for prevention of cardiovascular disease and death: a systematic review and meta-analysis. Lancet. 2016;387:957–67.
- Adams R, Henry KE, Sridharan A, et al. Prospective, multi-site study of patient outcomes after implementation of the TREWS machine learning-based early warning system for sepsis. Nat Med. 2022;28:1455–60.
- Escobar GJ, Liu VX, Schuler A, et al. Automated identification of adults at risk for in-hospital clinical deterioration. N Engl J Med. 2020;383:1951–60.
- Romero-Brufau S, Wyatt KD, Boyum P, et al. Implementation of artificial intelligence-based clinical decision support to reduce hospital readmissions at a regional hospital. Appl Clin Inform. 2020;11:570–7. https://doi.org/10.1055/s-0040-1715827
- UK Prospective Diabetes Study Group. Intensive blood-glucose control with sulphonylureas or insulin compared with conventional treatment and risk of complications in patients with type 2 diabetes (UKPDS 33). Lancet. 1998;352:837–53.
- Geruso M, Layton TJ, Wallace J. What difference does a health plan make? Evidence from random plan assignment in Medicaid. Am Econ J Appl Econ. 2023;15:341–79.
- Office of Inspector General. Some Medicare Advantage organization denials of prior authorization requests raise concerns about beneficiary access to medically necessary care. OIG Report OEI-09-18-00260. 2022.
- Brodeur P, Koshy JM, Palepu A, et al. A prospective clinical feasibility study of a conversational diagnostic AI in an ambulatory primary care clinic. arXiv preprint arXiv:2603.08448. 2026.
- Kangovi S, Mitra N, Norton L, et al. Effect of community health worker support on clinical outcomes of low-income patients across primary care facilities: a randomized clinical trial. JAMA Intern Med. 2018;178:1635–43.
- Reed ME, Huang J, Somers M, et al. Telemedicine versus in-person primary care: treatment and follow-up visits. Ann Intern Med. 2023;176:1349–57.
- Sax DR, Kene MV, Huang J, et al. Downstream emergency department and hospital utilization comparably low following in-person versus telemedicine primary care for high-risk conditions. J Gen Intern Med. 2024;39:2446–53.
