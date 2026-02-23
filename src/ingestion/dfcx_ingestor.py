# src/ingestion/dfcx_ingestor.py
# Simulates extraction of prompts from Dialogflow CX generators
# In real GCP: would use google-cloud-dialogflow-cx SDK
# API call would be: dfcx_client.get_generator(name=generator_path)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.registry.store import PromptRegistry


def get_dfcx_sample_prompts() -> list:
    """
    Returns sample DFCX generator prompts.
    In production: these would be extracted via Dialogflow CX API
    from actual generator configurations in your DFCX agent.
    """
    return [
        {
            "name": "billing_payment_query",
            "domain": "billing",
            "agent_type": "dfcx",
            "environment": "dev",
            "system_instructions": (
                "You are a billing support assistant for a telecom company. "
                "Always be polite, concise, and empathetic. "
                "Never share sensitive payment details in plain text. "
                "If you cannot resolve the issue, escalate to a human agent."
            ),
            "template": (
                "Customer has a query about: {issue_type}\n"
                "Account ID: {account_id}\n"
                "Last payment date: {last_payment_date}\n\n"
                "Provide a clear resolution or next steps for the customer."
            ),
            "model_parameters": {
                "model": "gemini-1.5-pro",
                "temperature": 0.3,
                "max_output_tokens": 512,
                "top_p": 0.8,
                "top_k": 20
            },
            "metadata": {
                "source_agent": "telecom-billing-agent-v2",
                "generator_id": "gen-billing-001",
                "dfcx_project": "telecom-cx-project",
                "extracted_by": "dfcx_ingestor"
            }
        }
    ]


def ingest_dfcx_prompts():
    """
    Ingest all DFCX prompts into the central registry.
    Skips prompts that already exist (idempotent operation).
    """
    registry = PromptRegistry()
    prompts = get_dfcx_sample_prompts()
    ingested = []

    for p in prompts:
        try:
            result = registry.create_prompt(
                name=p["name"],
                domain=p["domain"],
                agent_type=p["agent_type"],
                environment=p["environment"],
                system_instructions=p["system_instructions"],
                template=p["template"],
                model_parameters=p["model_parameters"],
                metadata=p["metadata"]
            )
            ingested.append(result["prompt_id"])
        except ValueError as e:
            print(f"[SKIPPED] {p['name']} - already exists: {e}")

    print(f"\n[DFCX] Ingested {len(ingested)} prompt(s): {ingested}")
    return ingested


if __name__ == "__main__":
    ingest_dfcx_prompts()