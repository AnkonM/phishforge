"""
Live smoke test: one live call to the Gemini API using finance_invoice_fraud.json
via the production generate() interface. Saves output to smoke_test_output.json.
"""
import json
import os
import sys

# Load .env
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

sys.path.insert(0, ".")
import config
from models.schemas.scenario import ScenarioSpecification
from core.generation.generator import generate

spec_path = "scenarios/examples/finance_invoice_fraud.json"
with open(spec_path, "r", encoding="utf-8") as f:
    spec = ScenarioSpecification(**json.load(f))

print("Running live smoke test...")
print(f"Scenario ID: {spec.scenario_id}")
print(f"Model: {config.MODEL_NAME}")

result = generate(spec)
output_dict = result.model_dump(mode="json")

output_file = "smoke_test_output.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_dict, f, indent=2, default=str)

print(f"SUCCESS: Saved validated simulation to {output_file}")
print("\n--- VALIDATED OUTPUT SUMMARY ---")
print(f"Subject: {result.subject}")
print(f"Sender: {result.sender}")
print(f"Intended Indicators: {result.intended_indicators}")
print(f"Model: {result.model}")
print(f"Prompt Version: {result.prompt_version}")
print(f"Timestamp: {result.timestamp}")
