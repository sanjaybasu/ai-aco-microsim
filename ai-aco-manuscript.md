# Would an AI-First Accountable Care Organization Improve Patient Outcomes in Medicaid?

### A Multi-Agent AI Debate and Validated Microsimulation Study

Sanjay Basu, M.D., Ph.D.,<sup>1,2</sup> and Rajaie Batniji, M.D., Ph.D.<sup>1</sup>

<sup>1</sup>Waymark, San Francisco, CA; <sup>2</sup>University of California San Francisco, San Francisco, CA

Address reprint requests to Dr. Basu at sanjay.basu@waymarkcare.com.

---

## Abstract

**Background**: Medicaid managed care serves over 70% of beneficiaries, yet preventable acute care utilization remains high and racial disparities persist. Whether an AI-first accountable care organization — combining virtual primary care, automated administrative functions, and community health worker outreach — could improve patient outcomes has not been rigorously evaluated.

**Methods**: We used a Modified Delphi process with 8 AI agents — spanning clinical safety, actuarial soundness, regulatory feasibility, patient advocacy, and health equity — to design an AI-first Medicaid ACO through iterative convergence. We evaluated the consensus via Monte Carlo microsimulation on 75,043 Medicaid adults nationally (1,000-iteration probabilistic sensitivity analysis, 7 scenarios), validated through backtesting against five independent natural experiments. Primary outcomes were hospitalizations, emergency department visits, and preventive care quality (HEDIS gap closure). Structural sensitivity analysis isolated administrative reform from AI clinical efficacy.

**Results**: Backtesting against 5 past delivery reforms showed 100% coverage (15/15 outcome measures within observed confidence intervals) with a calibration ratio of 0.99. Under consensus parameters, the AI ACO would be expected to decrease hospitalizations by 15 per 1,000 person-years (95% uncertainty interval [UI], 7 to 24), reduce emergency department visits by 39 per 1,000 person-years (95% UI, 20 to 63), and improve HEDIS gap closure from 35% to 50%. Improvements were observed across all racial groups. Per-member-per-month costs would be expected to fall by $41 total (95% UI, $16 to $76), of which $27 (66%) derived from administrative automation alone — requiring no assumptions about AI clinical efficacy. A provider rate sensitivity analysis incorporating network adequacy effects showed that 91% of clinical benefit was retained even without raising reimbursement above current Medicaid levels. The model achieved net improvement with greater than 50% probability when administrative overhead remained below 7% of premium.

**Conclusions**: An AI-driven Medicaid ACO model shows potential for improved patient outcomes under identifiable conditions. Financial viability depends primarily on administrative efficiency rather than AI clinical performance, suggesting that delivery reform merits evaluation through Section 1115 demonstration waivers.

---

## Introduction

Nearly 40% of acute care visits among 48.3 million Medicaid beneficiaries are for ambulatory care-sensitive conditions — hospitalizations and emergency department (ED) visits manageable through timely primary care.<sup>1</sup> This rate varies 13-fold across counties, indicating delivery failures rather than immutable patient characteristics.<sup>1</sup> Medicaid managed care organizations (MCOs), enrolling over 70% of beneficiaries,<sup>2</sup> have not demonstrated consistent outcome improvements: reviews find mixed effects,<sup>3</sup> causal analyses show mandatory managed care increased spending without improving outcomes,<sup>4</sup> random plan assignment reveals no quality differentiation,<sup>30</sup> and managed care has widened racial disparities.<sup>5</sup> The information asymmetry Arrow identified as healthcare's foundational market failure<sup>6</sup> remains unresolved: administrative overhead averages 8 to 13% of premium,<sup>7,8</sup> fewer than half of physicians accept new Medicaid patients,<sup>10</sup> and over half of listed Medicaid providers are unreachable or not accepting patients.<sup>9</sup> Medicaid thus presents the most acute case for delivery reform: the population faces the greatest access barriers, disparities are widest, and state-level Section 1115 demonstration waivers provide a regulatory pathway for structural innovation without requiring federal legislation.

AI clinical decision support offers an alternative approach. Large language models achieve expert-level diagnostic performance,<sup>11</sup> a conversational AI was rated superior to physicians on 30 of 32 axes,<sup>12</sup> and a prospective feasibility study found 90% diagnostic accuracy with zero safety stops triggered.<sup>31</sup> A cluster-randomized trial of a guideline-based clinical decision support system for hypertension improved concordant treatment by 15.2 percentage points (N = 12,137).<sup>13</sup> However, general-purpose AI health tools under-triaged 52% of emergency presentations,<sup>14</sup> underscoring the distinction between purpose-built clinical AI and consumer tools.<sup>15</sup> The question is whether AI can address Arrow's information asymmetry<sup>6</sup> not merely at the point of care but at the organizational level — replacing administrative functions that consume resources without improving outcomes.

An accountable care organization, rather than AI deployed within existing MCOs, addresses the structural problem: MCO administrative overhead persists regardless of clinical tools added to it, whereas an ACO can replace both clinical delivery and administrative functions within a single accountable entity. ACOs have demonstrated savings in Medicare<sup>16,17</sup> and Medicaid,<sup>18,19</sup> but no model combines AI clinical delivery with streamlined administration. Designing such a model requires simultaneous optimization across interdependent clinical, regulatory, financial, and ethical domains — a task poorly suited to individual expert opinion but well-matched to multi-agent debate, which improves reasoning through structured adversarial deliberation.<sup>20,36</sup> We adapted this framework to healthcare system design, then evaluated the consensus through calibrated microsimulation with patient outcomes as primary endpoints.

## Methods

### Study Design and Reporting

This study combined structured AI-assisted organizational design with Monte Carlo microsimulation evaluation (Figure 1). We followed the Consolidated Health Economic Evaluation Reporting Standards 2022 (CHEERS 2022).<sup>21</sup>

### Multi-Agent Debate

We adapted the multi-agent ensemble debate framework<sup>20,36</sup> to healthcare system design. Eight AI agents were instantiated with expert personas (Table S1) representing dimensions MACPAC identifies as critical for Medicaid managed care evaluation<sup>8</sup> — access, quality, cost, beneficiary experience — along with regulatory, ethical, and organizational feasibility (Supplementary Appendix A).

Each agent independently designed a complete AI ACO across 12 parameter domains (Table S4): clinical model, payment structure, provider reimbursement, organizational structure, regulatory pathway, quality framework, AI clinical architecture, human oversight, SDOH integration, rural/urban design, anti-monopoly provisions, and ethical governance. Nine domains correspond to CMS requirements for managed care approval and 1115 waiver evaluation<sup>37</sup>; three (AI architecture, human oversight, ethical governance) address challenges specific to AI-delivered care. Agents followed a Modified Delphi process<sup>38</sup>: after independent proposals (Round 0), each agent received anonymized group summary statistics with their position highlighted, and agents outside the IQR were required to justify or revise. Convergence required IQR stability or ≥75% categorical agreement across consecutive rounds (Supplementary Appendix A). Agents diverging by more than 1 SD from consensus filed minority reports parameterizing sensitivity scenarios. All agents used Claude Sonnet (Anthropic) with temperature 0.7; convergence was robust to temperature variation (Supplementary Appendix B).

### Study Population

The study population comprised 75,043 Medicaid adults aged 19 to 64 from the American Community Survey (ACS) Public Use Microdata Sample (PUMS), 2019–2023, representing approximately 6.8 million non-institutionalized Medicaid adults nationally (Table S2). Digital access was modeled using race-by-metropolitan-status broadband penetration rates from Pew Research Center and Federal Communications Commission data,<sup>22</sup> ranging from 45% for American Indian/Alaska Native (AIAN) adults in nonmetropolitan areas to 87% for White adults in metropolitan areas.

### Microsimulation Model

The microsimulation modeled each individual through 5 sequential stages (Figure 1, right panel): (1) Digital Access — whether each individual could and would access virtual care, based on broadband and technology adoption rates by race and metropolitan status<sup>22</sup>; (2) Care Engagement — sequential probabilities of outreach, agreement, engagement, and adherence, with racial penalties calibrated from AHRQ data and a 50% engagement penalty for individuals without broadband, anchored to observed telehealth disparities among patients with limited English proficiency<sup>23,24</sup>; (3) Clinical Utilization — risk-stratified hospitalization, ED, and primary care rates from MEPS and HCUP, modified by relative risk reductions anchored to evidence linking clinical decision support to chronic disease management improvements with established dose-response relationships to acute events<sup>13</sup>; (4) Preventive Care Quality — HEDIS gap closure rates from NCQA benchmarks; and (5) Equity — condition detection and documentation probabilities by race reflecting differential claims visibility.<sup>25</sup> All parameters were drawn from Beta and Gamma distributions in each of 1,000 PSA iterations (Table S3). Administrative overhead was modeled at 8.3% for MCOs and 3.0% for the AI ACO, the latter reflecting automation of high-volume functions (claims adjudication, prior authorization, eligibility verification) consistent with traditional Medicaid administrative rates.<sup>7,26</sup>

### Scenarios

Seven scenarios were compared (Table S5): status quo MCO (S0), AI ACO consensus (S1), optimistic (S2), and pessimistic (S3) applying debate consensus, upper-bound, and minority-report parameters; care coordination without AI (S4); AI ACO under universal eligibility (S5); and administrative reform only (S6), which applied 3% overhead with identical clinical parameters to S0, isolating administrative from clinical effects.

### Calibration

The status quo scenario was calibrated to published Medicaid benchmarks (Table S6): per-member-per-month (PMPM) costs from MACPAC MACStats,<sup>8</sup> hospitalization and ED rates from HCUP and MEPS, HEDIS scores from NCQA state profiles, and administrative cost shares from CMS Medical Loss Ratio reports.<sup>7</sup>

### External Validation

The microsimulation was validated through backtesting against five natural experiments: Oregon CCOs (global budgets),<sup>18</sup> Pioneer ACOs (shared savings),<sup>16,17</sup> CHW randomized trials,<sup>27</sup> MSSP (weak shared savings),<sup>17</sup> and CPC+ (primary care transformation; negative control).<sup>28</sup> For each, the model was run with matching parameters and compared across 3 metrics (15 total comparisons; Figure 2, Table S10). Administrative projections were benchmarked against single-payer systems.<sup>26</sup>

### Welfare Analysis

Net social surplus was computed using a Hicks-Kaldor framework<sup>34</sup>: consumer surplus (QALYs at $100,000 willingness-to-pay), government surplus (utilization savings plus administrative overhead reduction), and producer surplus (net provider revenue change). QALYs were estimated from changes in acute care events using standard disability weights: 0.05 QALYs per hospitalization averted and 0.01 per ED visit averted, consistent with Global Burden of Disease disability-adjusted life year methods (Supplementary Appendix C). Equity weighting used the Atkinson inequality-aversion parameter<sup>35</sup> (Supplementary Appendix C).

### Statistical Analysis

PSA (N = 1,000 iterations) drew all parameters from specified distributions (Table S3). Threshold analyses varied the AI administrative cost rate from 3% to 10%. A provider rate sensitivity analysis modeled the pathway from reimbursement rates through network participation to patient outcomes, parameterized as a logistic function calibrated to empirical Medicaid appointment availability data.<sup>32</sup> Only non-AI encounters (42%) were affected; AI encounters were rate-independent. An encounter share sensitivity analysis varied AI encounter proportion from 20% to 75% (Supplementary Appendix G). All analyses used ACS person weights (PWGTP).

## Results

### Debate Convergence

In Round 0, agents agreed on regulatory pathway (100%, Section 1115 waiver), provider rates (IQR: 120–125% of Medicare), and AI architecture (100%, multi-model ensemble). The most contested domains were human oversight (CV = 0.39), clinical model scope (CV = 0.21), and rural/urban delivery (CV = 0.15) (Figure 3). By Round 2, all 12 domains met Delphi convergence criteria and 11 of 12 met CV < 0.15, with human oversight (CV = 0.23) reflecting genuine disagreement about supervision intensity (Supplementary Appendix A).

### AI ACO Consensus Design

The consensus specified (Table S4): AI-first virtual primary care handling 58% of encounters with physician oversight at 1:45; a 3-model ensemble architecture with mandatory escalation for high-acuity conditions; full capitation at $438 PMPM with two-sided risk sharing; community health workers at 2.5 per 1,000 members; FQHC referral for all physical examinations; mandatory quarterly algorithmic bias auditing; an independent ethics board with binding halt authority; and prohibition on for-profit conversion. Provider reimbursement was set at 125% of Medicare for primary care and 110% for hospital services, funded by administrative overhead reduction from 8.3% to 3.0%.

Four minority reports parameterized the pessimistic scenario (S3): concerns that the AI encounter rate was too high for complex patients, that bias auditing lacked enforcement mechanisms, that opt-out enrollment may feel coercive for Medicaid beneficiaries, and that the 3.0% administrative target may underestimate edge-case costs (Supplementary Appendix A).

### Validation

The status quo scenario calibrated within published ranges for all 5 metrics (Table S6). In backtesting against 5 independent natural experiments — spanning global budgets, shared savings, community health worker engagement, and primary care transformation — the observed effect fell within the simulated 95% UI in 15 of 15 comparisons (100% coverage; Figure 2). The mean calibration ratio was 0.99 and mean absolute error was 1.1 percentage points. The model correctly reproduced both large reform effects (Oregon CCO: 7% spending reduction; CHW trials: 9% hospitalization reduction) and near-null effects (CPC+: 0% spending change), demonstrating calibration across the full range of delivery reform mechanisms.

### Patient Outcomes

Under the consensus design, the AI ACO would be expected to decrease hospitalizations by 15 per 1,000 person-years (95% UI, 7 to 24) and ED visits by 39 per 1,000 person-years (95% UI, 20 to 63) (Table). HEDIS gap closure would improve from 35% to 50%. Primary care visits increased, consistent with substitution from acute to preventive care. These reductions were driven by algorithmically prioritized outreach and 24/7 virtual availability increasing engagement from 12% to 21%, combined with AI clinical decision support improving care quality for engaged patients. The pessimistic scenario showed attenuated but directionally consistent improvements (10 fewer hospitalizations, 24 fewer ED visits per 1,000 person-years). Improvements were observed across all racial groups, with slightly larger absolute reductions among Black and AIAN adults (17 per 1,000) than White (14 per 1,000) and Hispanic adults (15 per 1,000). The Black-White hospitalization gap narrowed from 40 to 37 per 1,000 (8% reduction) and the AIAN-White gap from 51 to 48 (6% reduction). Stratification by race and metropolitan status showed improvements in all 8 subgroups with no widening of within-group gaps (Supplementary Appendix D; Figure S1).

### Cost and Administrative Efficiency

PMPM costs would be expected to fall by $41 (95% UI, $16 to $76), from $478 to $437 (Table). The administrative-reform-only scenario — which assumed zero AI clinical efficacy — would be expected to reduce PMPM by $27 (95% UI, $3 to $63), accounting for 66% of total savings. These administrative savings derived from automating claims adjudication, prior authorization processing, eligibility verification, and care management triage — high-volume functions currently requiring manual review — reducing overhead from 8.4% to 2.9% of premium, consistent with administrative cost rates in traditional (non-MCO) Medicaid programs (2 to 4%).<sup>7,26</sup> The remaining $14 PMPM (34%) derived from clinical performance improvements. The probability that administrative reform alone produced positive savings was 98.8%.

### Welfare and Equity

Net social surplus would be expected to be $646 per member per year (Figure S2), comprising: consumer surplus from health gains ($151; ~0.015 QALYs per member per year), government savings ($490; $176 from reduced utilization, $314 from administrative reduction), and producer surplus ($5). Net surplus was positive at all willingness-to-pay thresholds tested ($50,000 to $200,000 per QALY; Table S7). Equity-weighted welfare showed gains across all racial groups, though the digital divide attenuated gains for AIAN adults in nonmetropolitan areas (45% broadband penetration).

### Conditions for Improvement

The threshold analysis identified administrative cost rate as the dominant determinant (Spearman rho = 0.89 with PMPM savings). Figure 4 shows the probability of net improvement by administrative cost rate: at 3%, probability was 100%; at 6%, 78%; at 7%, 61%; at 8% (MCO baseline), 45%. AI-specific clinical parameters contributed minimally (combined rho < 0.25). A provider rate sensitivity analysis<sup>32</sup> showed the AI ACO retained 91% of its hospitalization reduction even without raising rates above current Medicaid levels (75% of Medicare), because 58% of encounters were rate-independent. Even the most conservative scenario (20% AI encounters, 75% Medicare rates) projected positive net savings (Supplementary Appendix F).

## Discussion

This study demonstrates that multi-agent AI debate can produce specific, internally consistent organizational designs for healthcare delivery reform, and that the resulting AI-driven Medicaid ACO shows potential for improved patient outcomes under identifiable conditions. Projected reductions are consistent with those observed in Oregon's CCO reform<sup>18</sup> and Medicare ACO programs.<sup>16,17,29</sup>

The projected $41 PMPM savings (8.6%) exceed Medicare ACO savings (1 to 3%),<sup>17,29</sup> but the primary mechanism differs: the AI ACO replaces administrative infrastructure rather than operating within it. The administrative-reform-only scenario isolates this — $27 PMPM derives from reducing overhead from 8.4% to 2.9% with no assumed AI clinical efficacy. The remaining $14 PMPM from clinical improvements falls within observed ACO effect ranges. This distinction matters because AI clinical evidence, while growing — including 90% diagnostic accuracy in a prospective feasibility study<sup>31</sup> — remains largely from controlled evaluations, and safety limitations of general-purpose AI tools are documented.<sup>14</sup>

The threshold analysis identifies a clear target: improvement with high probability when overhead remains below 5 to 6% — ambitious relative to MCOs (8 to 13%) but consistent with traditional Medicaid (2 to 4%) and single-payer systems.<sup>7,8,26</sup> This capitated approach also avoids unresolved questions about physician reimbursement as AI automates cognitive work under fee-for-service payment.<sup>33</sup>

Rapid Delphi convergence (3 rounds) could reflect shared training priors; however, agents operated under conflicting constraints (Table S1), produced measurable IQR narrowing on contested parameters, and achieved quantitative precision that human Delphi panels rarely reach. The design addresses Medicaid access barriers — fewer than half of physicians accept new Medicaid patients — through 24/7 virtual primary care with physician oversight and ensemble architecture that escalates uncertainty. The design is compatible with implementation by existing MCOs, health plans, or FQHC-based ACOs under Section 1115 waiver authority.

This study has several limitations. The microsimulation uses public survey data rather than claims-level data. Projected clinical improvements have not been directly observed for an AI-driven delivery model. Three of five backtests used Medicare populations; although comparisons use relative changes through shared mechanisms, Medicaid-specific validation is limited. The digital divide is modeled through broadband access and a 50% engagement penalty<sup>23,24</sup> but digital health literacy is not independently parameterized. The Modified Delphi uses instances of the same LLM, which is not equivalent to independent expert deliberation, though conflicting constraints produced genuine disagreement. The model captures steady-state effects; learning curves, trust accrual, and workforce adaptation are not modeled. Patient willingness to engage with AI care is modeled through the engagement cascade rather than direct evidence from Medicaid beneficiaries. AI clinical models may exhibit differential diagnostic accuracy by race<sup>25</sup>; the specified bias auditing has not been empirically tested as mitigation. Equity improvements are modest because the intervention operates within existing structural determinants of health disparities.

An AI-driven Medicaid ACO shows potential for improved patient outcomes and reduced costs under identifiable conditions, with financial viability primarily contingent on administrative efficiency. These findings support evaluation of AI-augmented delivery models through Section 1115 demonstration waivers, whether implemented by new entities or adopted within existing managed care organizations.

---

**Data and Code Availability**: All code for the multi-agent debate, microsimulation, welfare analysis, and figure generation is available at https://github.com/sanjaybasu/ai-aco-microsim. The ACS PUMS data are publicly available from the U.S. Census Bureau.

---

## References

1. Patel SY, Baum A, Basu S. Geographic variations and facility determinants of acute care utilization and spending for ambulatory care-sensitive conditions. Am J Manag Care 2024;30:e329-36.
2. Duggan M, Hayford T. Has the shift to managed care reduced Medicaid expenditures? Evidence from state and local-level mandates. J Policy Anal Manage 2013;32:505-35.
3. Montoya DF, Chehal PK, Adams EK. Medicaid managed care's effects on costs, access, and quality: an update. Annu Rev Public Health 2020;41:537-49.
4. Duggan M. Does contracting out increase the efficiency of government programs? Evidence from Medicaid HMOs. J Public Econ 2004;88:2549-72.
5. Kuziemko I, Meckel K, Rossin-Slater M. Does managed care widen infant health disparities? Evidence from Texas Medicaid. Am Econ J Econ Policy 2018;10:255-83.
6. Arrow KJ. Uncertainty and the welfare economics of medical care. Am Econ Rev 1963;53:941-73.
7. Centers for Medicare & Medicaid Services. Medical loss ratio annual reporting. 2024. (https://www.cms.gov/cciio/resources/data-resources/mlr).
8. Medicaid and CHIP Payment and Access Commission. MACStats: Medicaid and CHIP data book. 2024. (https://www.macpac.gov/macstats/).
9. Zhu JM, Myers R, McConnell KJ, Levine S, Polsky D. Phantom networks: discrepancies between reported and realized mental health care access in Oregon Medicaid. Health Aff (Millwood) 2022;41:1013-20. DOI: 10.1377/hlthaff.2022.00052.
10. Hsiang WR, Lukasiewicz A, Gentry M, et al. Medicaid patients have greater difficulty scheduling health care appointments compared with private insurance patients: a meta-analysis. Inquiry 2019;56:46958019838118.
11. Singhal K, Tu T, Gottweis J, et al. Toward expert-level medical question answering with large language models. Nat Med 2025;31:943-50.
12. Tu T, Schaekermann M, Palepu A, et al. Towards conversational diagnostic artificial intelligence. Nature 2025;642:442-50.
13. Song J, Wang X, Wang B, et al. Learning implementation of a guideline based decision support system to improve hypertension treatment in primary care in China: pragmatic cluster randomised controlled trial. BMJ 2024;386:e079143.
14. Ramaswamy A, Tyagi A, Hugo H, et al. ChatGPT Health performance in a structured test of triage recommendations. Nat Med 2026 (published online ahead of print Feb 23).
15. Basu S, Sheth P, Muralidharan B, Elamaran N, Kinra A, Morgan J, Batniji R. Comparative evaluation of AI architectures for medical triage safety: a real-world validation study. JMIR Preprints 2026. doi:10.2196/preprints.94081. Preprint.
16. Bond AM, Civelek Y, Schpero WL, et al. Long-term spending of accountable care organizations in the Medicare Shared Savings Program. JAMA 2025;333:1897-905.
17. McWilliams JM, Hatfield LA, Landon BE, Hamed P, Chernew ME. Medicare spending after 3 years of the Medicare Shared Savings Program. N Engl J Med 2018;379:1139-49.
18. McConnell KJ, Renfro S, Lindrooth RC, Cohen DJ, Wallace NT, Chernew ME. Oregon's Medicaid reform and transition to global budgets were associated with reductions in expenditures. Health Aff (Millwood) 2017;36:451-9.
19. Holm J, Pagan JA, Silver D. The impact of Medicaid accountable care organizations on health care utilization and spending: a scoping review. Med Care Res Rev 2024;81:355-69.
20. Du Y, Li S, Torralba A, Tenenbaum JB, Mordatch I. Improving factuality and reasoning in language models through multiagent debate. In: Proceedings of the 41st International Conference on Machine Learning (ICML). 2024:11733-63.
21. Husereau D, Drummond M, Augustovski F, et al. Consolidated Health Economic Evaluation Reporting Standards 2022 (CHEERS 2022) statement: updated reporting guidance for health economic evaluations. Value Health 2022;25:3-9.
22. Pew Research Center. Internet/broadband fact sheet. 2024. (https://www.pewresearch.org/internet/fact-sheet/internet-broadband/).
23. Nouri S, Khoong EC, Lyles CR, Karliner L. Addressing equity in telemedicine for chronic disease management during the Covid-19 pandemic. NEJM Catalyst 2020;1(3).
24. Rodriguez JA, Khoong EC, Lipsitz SR, Lyles CR, Bates DW, Samal L. Telehealth experience among patients with limited English proficiency. JAMA Netw Open 2024;7:e2410691.
25. Obermeyer Z, Powers B, Vogeli C, Mullainathan S. Dissecting racial bias in an algorithm used to manage the health of populations. Science 2019;366:447-53.
26. Himmelstein DU, Campbell T, Woolhandler S. Health care administrative costs in the United States and Canada, 2017. Ann Intern Med 2020;172:134-42.
27. Vasan A, Morgan JW, Mitra N, et al. Effects of a standardized community health worker intervention on hospitalization among disadvantaged patients with multiple chronic conditions: a pooled analysis of three clinical trials. Health Serv Res 2020;55(Suppl 2):894-901.
28. Singh P, Fu N, Dale S, et al. The Comprehensive Primary Care Plus model and health care spending, service use, and quality. JAMA 2024;331:132-46.
29. Sen AP, Chen LM, Samson LW, Epstein AM, Joynt Maddox KE. Performance in the Medicare Shared Savings Program by ACOs disproportionately serving dual and disabled populations. Med Care 2018;56:805-11.
30. Geruso M, Layton TJ, Wallace J. What difference does a health plan make? Evidence from random plan assignment in Medicaid. Am Econ J Appl Econ 2023;15:341-79.
31. Brodeur P, Koshy JM, Palepu A, et al. A prospective clinical feasibility study of a conversational diagnostic AI in an ambulatory primary care clinic. arXiv preprint arXiv:2603.08448. 2026.
32. Polsky D, Candon M, Saloner B, et al. Changes in primary care access between 2012 and 2016 for new patients with Medicaid and private coverage. JAMA Intern Med 2017;177:588-90.
33. Carrier ER, Augenstein J. How could artificial intelligence affect physician payment for nonprocedural services? (Part 1). Health Aff Forefront. March 10, 2026. doi:10.1377/forefront.20260309.834789.
34. Kaldor N. Welfare propositions of economics and interpersonal comparisons of utility. Econ J 1939;49:549-52.
35. Atkinson AB. On the measurement of inequality. J Econ Theory 1970;2:244-63.
36. Yuksekgonul M, Koceja D, Li X, et al. Learning to discover at test time. arXiv preprint arXiv:2601.16175. 2026.
37. Centers for Medicare & Medicaid Services. Medicaid and Children's Health Insurance Program (CHIP) programs; Medicaid managed care, CHIP delivered in managed care, and revisions related to third party liability. Final rule. 42 CFR Parts 431, 433, 438, 440, 457. Fed Regist 2016;81:27498-901.
38. Diamond IR, Grant RC, Feldman BM, et al. Defining consensus: a systematic review recommends methodologic criteria for reporting of Delphi studies. J Clin Epidemiol 2014;67:401-9.

**Table 1. Microsimulation Results: Patient Outcomes and Costs Across Scenarios.**

| Outcome | Status Quo MCO | AI ACO | AI ACO (Pessimistic) | Admin Reform Only | Care Coord. Only |
|---|---|---|---|---|---|
| **Patient outcomes** | | | | | |
| Hospitalizations per 1,000 PY (95% UI) | 191 (147–238) | 176 (135–220) | 181 (140–228) | 191 (147–240) | 181 (139–228) |
| ED visits per 1,000 PY (95% UI) | 702 (551–867) | 663 (519–817) | 678 (528–839) | 702 (548–865) | 681 (533–839) |
| PCP visits per 1,000 PY (95% UI) | 3,429 (2,709–4,236) | 3,549 (2,808–4,370) | 3,550 (2,795–4,366) | 3,429 (2,702–4,231) | 3,600 (2,835–4,443) |
| HEDIS gap closure, % (95% UI) | 35 (26–45) | 50 (41–60) | 42 (36–49) | 35 (26–45) | 37 (27–47) |
| Engagement rate, % (95% UI) | 12 (10–15) | 21 (12–33) | 21 (13–33) | 12 (10–15) | 14 (11–17) |
| **Cost and administration** | | | | | |
| PMPM, $ (95% UI) | 478 (377–593) | 437 (344–543) | 443 (348–548) | 451 (356–559) | 458 (360–567) |
| PMPM savings, $ (95% UI) | — | 41 (16–76) | 35 (11–70) | 27 (3–63) | 21 (12–35) |
| Admin costs, % of premium (95% UI) | 8.4 (6.0–14.5) | 2.9 (1.0–6.0) | 2.9 (1.0–6.0) | 2.9 (1.0–6.0) | 5.9 (4.0–10.2) |

Values are means from 1,000 probabilistic sensitivity analysis iterations with network adequacy modeling. Uncertainty intervals (95% UI) represent the 2.5th and 97.5th percentiles. PMPM savings are computed as paired iteration-level differences. ED denotes emergency department, HEDIS Healthcare Effectiveness Data and Information Set, MCO managed care organization, PCP primary care physician, PMPM per member per month, and PY person-years. "Care Coord. Only" denotes current MCO with added community health workers and care managers but no AI.

---

## Figure Legends

**Figure 1. Study Overview.** Two-phase design. Phase 1 (left): 8 AI agents with distinct expert personas independently propose AI ACO designs across 12 parameter domains, then engage in a Modified Delphi process (3 rounds) with iterative convergence assessment. Phase 2 (right): the consensus design is evaluated via 5-stage Monte Carlo microsimulation — digital access, care engagement, clinical utilization, preventive care quality, and equity — across 7 scenarios with 1,000-iteration probabilistic sensitivity analysis.

**Figure 2. Calibration and External Validation.** Left panel: simulated status quo values (dots with 95% UI whiskers) plotted against published Medicaid benchmark ranges (shaded bands) for PMPM cost, hospitalization rate, ED visit rate, HEDIS gap closure, and administrative cost share. Right panel: backtesting validation — the microsimulation was run with parameters matching five independent natural experiments (Oregon CCOs, Pioneer ACOs, CHW randomized trials, MSSP, and CPC+) and projected percent changes in spending, hospitalizations, and ED visits (dots with 95% UI) are plotted against observed effect sizes (diamonds with 95% CIs). The observed effect fell within the simulated 95% UI in 15 of 15 comparisons (100% coverage), with a mean calibration ratio of 0.99 and mean absolute error of 1.1 percentage points.

**Figure 3. Modified Delphi Convergence.** Coefficient of variation (CV) across 8 expert agents for each of 12 design parameter domains, shown by Delphi round. Domains below the dashed line (CV < 0.15) have converged. Nine domains converged from independent Round 0 proposals; the remaining domains converged through Delphi feedback rounds, with human oversight (CV = 0.23) as the only domain not reaching the strict CV threshold by Round 2.

**Figure 4. Conditions for Improvement: Probability of Net Savings by Administrative Cost Rate.** Analogous to a cost-effectiveness acceptability curve, the figure shows the probability that the AI ACO achieves net savings relative to the status quo MCO as a function of the AI ACO's administrative cost rate. At 3% (projected), probability is 100%; at 6%, 78%; at 7%, 61%; at 8% (equal to MCO baseline), 45%. The vertical dashed line marks the MCO baseline (~8%). The shaded region indicates the range of administrative costs observed in traditional (non-MCO) Medicaid programs (2 to 4%).
