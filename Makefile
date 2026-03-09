# AI ACO Microsimulation — Reproducible Pipeline
# ================================================
#
# Targets:
#   make setup          Install dependencies
#   make data           Download/prepare ACS PUMS data
#   make debate         Run multi-agent debate (requires ANTHROPIC_API_KEY)
#   make microsim       Run 1000-iteration PSA microsimulation
#   make welfare        Run welfare analysis
#   make figures        Generate manuscript figures
#   make all            Run full pipeline (debate → microsim → welfare → figures)
#   make microsim-only  Run microsim + welfare + figures (skip debate, use cached results)
#   make clean          Remove all generated output
#
# Prerequisites:
#   - Python 3.11+
#   - ACS PUMS data (see data/README.md)
#   - ANTHROPIC_API_KEY environment variable (for debate step only)

PYTHON ?= python3
N_ITERATIONS ?= 1000
OUTPUT_DIR ?= output

.PHONY: all setup data debate microsim welfare figures microsim-only clean

all: debate microsim welfare figures

setup:
	pip install -r requirements.txt

data:
	@echo "=== Preparing ACS PUMS data ==="
	@echo "See data/README.md for instructions on obtaining ACS PUMS data."
	@echo "Place acs_pums_medicaid_adults.parquet in ../medicaid-frailty-bias/data/"
	@test -f ../medicaid-frailty-bias/data/acs_pums_medicaid_adults.parquet || \
		(echo "ERROR: ACS PUMS data not found. Run the data download script first." && exit 1)
	@echo "Data found."

debate:
	@echo "=== Step 1: Multi-Agent Debate ==="
	@test -n "$$ANTHROPIC_API_KEY" || (echo "ERROR: ANTHROPIC_API_KEY not set" && exit 1)
	$(PYTHON) run_pipeline.py --debate-only --output-dir $(OUTPUT_DIR)

microsim:
	@echo "=== Step 2: Microsimulation PSA (N=$(N_ITERATIONS)) ==="
	$(PYTHON) run_pipeline.py --microsim-only --n-iterations $(N_ITERATIONS) --output-dir $(OUTPUT_DIR)

welfare: microsim
	@echo "=== Step 3: Welfare Analysis ==="
	@echo "(Welfare runs as part of microsim step)"

figures:
	@echo "=== Step 4: Generate Figures ==="
	$(PYTHON) -c "\
from visualization.exhibits import *; \
from pathlib import Path; \
import pandas as pd; \
figdir = Path('$(OUTPUT_DIR)/figures'); figdir.mkdir(parents=True, exist_ok=True); \
summary = pd.read_csv('$(OUTPUT_DIR)/microsim/psa_summary.csv'); \
psa = pd.read_parquet('$(OUTPUT_DIR)/microsim/psa_results_full.parquet'); \
welfare = pd.read_csv('$(OUTPUT_DIR)/welfare/welfare_analysis.csv'); \
plot_outcome_radar(summary, figdir / 'figure2_outcomes.pdf'); \
plot_equity_impact(psa, figdir / 'figure3_equity.pdf'); \
plot_welfare_waterfall(welfare, figdir / 'figure4_welfare.pdf'); \
print('Figures saved to', figdir); \
"

microsim-only: microsim figures
	@echo "=== Pipeline complete (microsim + welfare + figures) ==="

clean:
	rm -rf $(OUTPUT_DIR)/microsim $(OUTPUT_DIR)/welfare $(OUTPUT_DIR)/figures
	@echo "Output cleaned. Debate results preserved."
