#!/bin/bash
# Run the full multi-agent debate in background
# Usage: nohup bash run_debate.sh > debate_log.txt 2>&1 &
cd /Users/sanjaybasu/waymark-local/packaging/ai-aco
export ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY /Users/sanjaybasu/waymark-local/notebooks/waymark-ai-pcp/.env | cut -d= -f2)

/opt/anaconda3/bin/python -c "
from debate.engine import DebateEngine, DebateConfig, LLMConfig
import logging, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.FileHandler('output/debate/debate.log'), logging.StreamHandler()])

config = DebateConfig(
    max_rounds=6,
    convergence_cv_threshold=0.15,
    convergence_domains_required=10,
    convergence_stability_rounds=2,
    critique_sample_size=3,
    output_dir='output/debate',
    llm=LLMConfig(
        provider='anthropic',
        model_id='claude-sonnet-4-20250514',
        temperature=0.7,
        max_tokens=8192,
        rate_limit_delay=2.0,
    ),
)

engine = DebateEngine(config)
results = engine.run()

print(f'Total rounds: {results[\"total_rounds\"]}')
print(f'Converged: {results[\"converged\"]}')
print(f'Converged domains: {results[\"final_converged_domains\"]}')

with open('output/debate/debate_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
print('Results saved.')
"
