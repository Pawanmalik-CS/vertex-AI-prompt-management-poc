# src/utils/filter.py
# Filtering utility for the prompt registry
# Provides domain-based and environment-based filtering
# Core requirement: no cross-contamination between domains/environments

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.registry.store import PromptRegistry
from tabulate import tabulate


def display_prompts_table(prompts: list, title: str = ""):
    """
    Display prompts in a formatted table in the terminal.
    Shows key fields only for readability.
    """
    if not prompts:
        print(f"\n[FILTER] No prompts found for: {title}")
        return

    table_data = []
    for p in prompts:
        table_data.append([
            p["prompt_id"],
            p["domain"],
            p["agent_type"],
            p["environment"],
            f"v{p['current_version']}",
        ])

    headers = ["Prompt ID", "Domain", "Agent Type", "Environment", "Version"]

    print(f"\n{'=' * 70}")
    print(f"  {title}  ({len(prompts)} result(s))")
    print(f"{'=' * 70}")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def filter_by_domain(domain: str) -> list:
    """
    Return all prompts belonging to a specific domain.
    No prompts from other domains will appear (no cross-contamination).
    """
    registry = PromptRegistry()
    results = registry.list_prompts(domain=domain)
    display_prompts_table(results, f"Domain Filter: '{domain}'")
    return results


def filter_by_environment(environment: str) -> list:
    """
    Return all prompts belonging to a specific environment.
    No prompts from other environments will appear (no cross-contamination).
    """
    registry = PromptRegistry()
    results = registry.list_prompts(environment=environment)
    display_prompts_table(results, f"Environment Filter: '{environment}'")
    return results


def filter_by_domain_and_environment(domain: str, environment: str) -> list:
    """
    Return prompts matching BOTH domain AND environment.
    Most precise filter - used before migration to verify source prompts.
    """
    registry = PromptRegistry()
    results = registry.list_prompts(domain=domain, environment=environment)
    display_prompts_table(
        results,
        f"Domain: '{domain}' + Environment: '{environment}'"
    )
    return results


def list_all_prompts() -> list:
    """Return and display all prompts in the registry."""
    registry = PromptRegistry()
    results = registry.list_prompts()
    display_prompts_table(results, "ALL PROMPTS IN REGISTRY")
    return results


if __name__ == "__main__":
    # Demo: run all filter scenarios
    print("\n>>> TEST 1: List ALL prompts")
    list_all_prompts()

    print("\n>>> TEST 2: Filter by domain = 'billing'")
    filter_by_domain("billing")

    print("\n>>> TEST 3: Filter by domain = 'tech_support'")
    filter_by_domain("tech_support")

    print("\n>>> TEST 4: Filter by environment = 'dev'")
    filter_by_environment("dev")

    print("\n>>> TEST 5: Filter by domain='shared' + environment='dev'")
    filter_by_domain_and_environment("shared", "dev")

    print("\n>>> TEST 6: Filter by domain='billing' + environment='prod'")
    print("(Should return 0 results - no cross contamination)")
    filter_by_domain_and_environment("billing", "prod")