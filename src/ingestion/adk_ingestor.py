# src/ingestion/adk_ingestor.py
# Simulates extraction of prompts from ADK (Agent Development Kit) agent configs
# In real setup: ADK agents store prompts in YAML/JSON config files
# This ingestor reads those configs and pushes to central registry

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.registry.store import PromptRegistry


def get_adk_sample_prompts() -> list:
    """
    Returns sample ADK agent prompts.
    In production: these would be parsed from ADK agent YAML config files.
    
    Example ADK config structure:
        agent:
          name: tech-support-agent
          model: gemini-1.5-pro
          system_prompt: |
            You are a technical support agent...
    """
    return [
        {
            "name": "tech_support_troubleshoot",
            "domain": "tech_support",
            "agent_type": "adk",
            "environment": "dev",
            "system_instructions": (
                "You are a technical support specialist. "
                "Guide customers step by step through troubleshooting. "
                "Always confirm the issue is resolved before closing. "
                "Use simple, non-technical language unless the customer is technical. "
                "Log all steps taken for audit purposes."
            ),
            "template": (
                "Customer reported issue: {issue_description}\n"
                "Device type: {device_type}\n"
                "OS version: {os_version}\n"
                "Previous troubleshooting attempts: {previous_steps}\n\n"
                "Provide a structured troubleshooting guide with numbered steps."
            ),
            "model_parameters": {
                "model": "gemini-1.5-pro",
                "temperature": 0.2,
                "max_output_tokens": 1024,
                "top_p": 0.9,
                "top_k": 40
            },
            "metadata": {
                "source_agent": "adk-tech-support-v1",
                "config_file": "agents/tech_support/agent.yaml",
                "adk_version": "1.2.0",
                "extracted_by": "adk_ingestor"
            }
        }
    ]


def ingest_adk_prompts():
    """
    Ingest all ADK prompts into the central registry.
    Skips prompts that already exist (idempotent operation).
    """
    registry = PromptRegistry()
    prompts = get_adk_sample_prompts()
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

    print(f"\n[ADK] Ingested {len(ingested)} prompt(s): {ingested}")
    return ingested


if __name__ == "__main__":
    ingest_adk_prompts()