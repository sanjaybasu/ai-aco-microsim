# ai-aco-microsim

## Overview

This repository contains code to:

1. **Multi-agent debate**: 8 AI agents with distinct expert perspectives design an AI-driven Medicaid ACO across 12 parameter domains through structured critique and convergence
2. **Microsimulation**: 5-channel Monte Carlo simulation evaluating 7 scenarios on cost, quality, equity, and engagement
3. **Welfare analysis**: Hicks-Kaldor social surplus decomposition with equity weighting (Atkinson)
4. **Visualization**: Figures for the manuscript

## Reproducing Results

### Prerequisites

- Python 3.11+
- ~4 GB RAM (for 75,043-individual × 1,000-iteration PSA)
- ACS PUMS data (see [Data](#data) below)
- `ANTHROPIC_API_KEY` environment variable (for debate step only; microsimulation runs without it)

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run microsimulation + welfare + figures (uses cached debate consensus)
make microsim-only

# Or run full pipeline including debate
export ANTHROPIC_API_KEY=your-key-here
make all
```

### Step-by-Step

```bash
# Step 1: Multi-agent debate (requires Anthropic API key; ~30 min, ~$5 API cost)
python run_pipeline.py --debate-only

# Step 2: Microsimulation PSA (1,000 iterations; ~20 min on M1 Mac)
python run_pipeline.py --microsim-only --n-iterations 1000

# Step 3: Process results and generate figures
python process_results.py
```

## Data

### ACS PUMS (required)

The microsimulation uses American Community Survey Public Use Microdata Sample (PUMS) data, 2019–2023:

- **Source**: [Census Bureau ACS PUMS](https://www.census.gov/programs-surveys/acs/microdata.html)
- **Inclusion**: Age 19–64, Medicaid enrollment (HINS4 = 1), 17 states with complete data
- **N**: 75,043 individuals representing ~6.8 million Medicaid adults (population-weighted)
- **Format**: Parquet file at `../medicaid-frailty-bias/data/acs_pums_medicaid_adults.parquet`

To prepare the data, run the population loader from the companion frailty bias repository, or place a pre-built parquet file at the path above. The loader will create a synthetic population (N=10,000) for testing if the ACS data is not found.

### Parameter Sources (no download needed)

All microsimulation parameters are drawn from published sources coded directly in `microsim/parameters.py`:

| Parameter Domain | Source |
|---|---|
| Digital access rates | Pew Research Center 2024; FCC Broadband Maps |
| Engagement cascade | Vasan et al. Health Serv Res 2020; AHRQ NHQDR 2023 |
| Utilization rates | MEPS 2022; HCUP Statistical Briefs 2022 |
| Unit costs | HCUP 2022; MEPS 2022 |
| Quality (HEDIS) | NCQA State of Healthcare Quality 2024 |
| Administrative rates | CMS Medical Loss Ratio Reports 2024 |
| Equity (detection/cert) | Derived from ACS PUMS; Obermeyer et al. Science 2019 |

## Repository Structure

```
ai-aco-microsim/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── Makefile                   # Reproducible pipeline targets
├── run_pipeline.py            # Full end-to-end orchestrator
├── process_results.py         # Post-processing (debate → microsim → figures)
│
├── debate/                    # Multi-agent debate framework
│   ├── engine.py              # Debate orchestration (rounds, convergence)
│   ├── personas.py            # 8 expert agent definitions + prompts
│   ├── domains.py             # 12 parameter domain schemas
│   ├── parser.py              # Structured JSON response parser
│   └── convergence.py         # CV-based convergence tracker
│
├── microsim/                  # Monte Carlo microsimulation
│   ├── channels.py            # 5-channel simulation engine + PSA runner
│   ├── parameters.py          # PSA distributions (Beta/Gamma, all sourced)
│   ├── population.py          # ACS PUMS population loader
│   └── welfare.py             # Hicks-Kaldor welfare + Atkinson equity
│
├── visualization/             # Manuscript figures
│   └── exhibits.py            # 4 NEJM AI figures (convergence, radar, equity, welfare)
│
├── output/                    # Generated results (not tracked in git)
│   ├── debate/                # Debate round JSONs + consensus
│   ├── microsim/              # PSA results (parquet + CSV)
│   ├── welfare/               # Welfare analysis CSVs
│   └── figures/               # PDF + PNG figures
│
├── manuscript.md              # NEJM AI submission text
├── appendix.md                # Supplementary appendix
└── cover_letter.md            # Submission cover letter
```

## Key Design Decisions

### Microsimulation Architecture

The 5-channel engine (`microsim/channels.py`) simulates each individual through:

1. **Access**: Digital access probability by race × metro status (Pew 2024; FCC broadband maps)
2. **Engagement**: 4-step cascade (outreach → agreement → engagement → adherence) with racial penalties and 50% engagement penalty for individuals without broadband access (Rodriguez et al. JAMA Netw Open 2024; Nouri et al. NEJM Catalyst 2020)
3. **Utilization/Cost**: Poisson-distributed events (hospitalizations, ED, PCP) by risk tier with per-individual AI encounter share conditioned on digital access (see below)
4. **Quality**: HEDIS gap closure with racial differential
5. **Equity**: Detection/certification probabilities by race (Obermeyer et al. Science 2019)

### Per-Individual AI Encounter Share (v2 — key methodological update)

The population-level AI encounter share (58%, consensus design) is distributed at the individual level based on each person's digital access status:

- **With broadband access**: Higher AI encounter share (~58% / mean_population_access, capped at 90%)
- **Without broadband access**: Near-zero AI encounter share (~5%, representing phone-only triage and scheduling)

This ensures the population mean remains at the consensus 58% while correctly concentrating clinical effects among digitally connected beneficiaries. Prior to this update (v1), the 58% share was applied uniformly, which understated the equity impact of the digital divide on clinical outcomes.

The Spearman rho of the admin rate difference (SQ admin - AI admin) with PMPM savings = 0.82 (with ACS PUMS data; reported as 0.89 in the manuscript which used a slightly different PSA prior). Both values confirm administrative overhead reduction as the dominant determinant.

### Probabilistic Sensitivity Analysis

- 1,000 iterations drawing all parameters from Beta/Gamma/Normal distributions
- `ai_encounter_share` now drawn from Beta(30, 22), mean ~0.577, SD ~0.058 (previously hardcoded at 0.58)
- 7 scenarios: status quo MCO, AI ACO (consensus/optimistic/pessimistic), enhanced FFS, AI ACO universal, admin-reform-only
- 95% uncertainty intervals from paired iteration-level differences (PMPM savings are computed per-iteration as SQ[i] − AI[i])
- Population-weighted using ACS person weights (PWGTP)
- Monte Carlo standard error for PMPM savings: ~$0.52 (well below reporting threshold)

### Welfare and Sensitivity Analyses

`microsim/welfare.py` provides:
- `compute_welfare()`: Hicks-Kaldor surplus decomposition
- `sensitivity_wtp()`: WTP threshold sensitivity ($50k–$200k/QALY)
- `sensitivity_qaly_weights()`: Grid over QALY decrements (hospitalization, ED, PCP)
- `sensitivity_epsilon()`: Atkinson equity-aversion sensitivity (epsilon = 0.5, 1.0, 2.0)
- `mc_standard_error()`: Monte Carlo SE per outcome and scenario

QALY weights: hospitalization 0.05, ED 0.01, PCP 0.002 per event. Consistent with Briggs et al. Value Health 2016 and Jiang et al. Med Decis Making 2017 for ambulatory-care-sensitive condition hospitalizations. See `sensitivity_qaly_weights()` for range analysis.

### Structural Sensitivity

The admin-reform-only scenario (S6) applies AI administrative cost reduction (3% overhead) with identical clinical parameters to the status quo, isolating administrative savings from AI clinical efficacy assumptions. P(positive net savings | admin reform only) = 97–99% across PSA iterations.

## Verification

The status quo scenario calibrates within published ranges (eTable 6 in appendix):

| Metric | Simulated | Published Range |
|---|---|---|
| PMPM | $483 | $450–$550 (MACPAC) |
| Hospitalizations/1,000 PY | 196 | 150–220 (HCUP/MEPS) |
| ED visits/1,000 PY | 715 | 550–850 (MEPS) |
| HEDIS gap closure | 35% | 30–45% (NCQA) |
| Admin cost (% premium) | 8.3% | 8–13% (CMS) |

Note: values above are from the synthetic population (N=10,000). The manuscript reports values from the full ACS PUMS population (N=75,043); results are consistent within rounding.

## Changelog

### v2 (April 2026)
- **channels.py**: Per-individual AI encounter share conditioned on digital access (previously uniform at 58%)
- **parameters.py**: `ai_encounter_share` is now a PSA Beta distribution; previously hardcoded
- **welfare.py**: Added `sensitivity_qaly_weights()`, `sensitivity_epsilon()`, `mc_standard_error()`; documented QALY weight sources
- **process_results.py**: Added `compute_parameter_importance()` with correct paired Spearman rho; added `admin_only` scenario; welfare call now runs all sensitivity analyses

### v1 (March 2026)
- Initial release

## License

This code is provided for scientific reproducibility. Please cite the manuscript if you use or adapt this code.
