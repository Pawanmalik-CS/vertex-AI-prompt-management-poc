# src/utils/versioning.py
# Demonstrates versioning and rollback capabilities
# Acceptance criteria: revert a prompt to prior version via single command

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.registry.store import PromptRegistry
from tabulate import tabulate


def show_version_history(prompt_id: str):
    """Display complete version history of a prompt."""
    registry = PromptRegistry()
    history = registry.get_version_history(prompt_id)

    print(f"\n{'=' * 65}")
    print(f"  VERSION HISTORY: {prompt_id}")
    print(f"{'=' * 65}")

    table_data = []
    for v in history:
        # Truncate long text for display
        instructions_preview = v["system_instructions"][:50] + "..."
        table_data.append([
            f"v{v['version']}",
            v["change_note"],
            v["created_by"],
            v["created_at"][:19].replace("T", " "),
            instructions_preview
        ])

    headers = ["Version", "Change Note", "Author", "Created At", "Instructions Preview"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Show which version is currently active
    prompt = registry.get_prompt(prompt_id)
    print(f"\n  >>> ACTIVE VERSION: v{prompt['current_version']} <<<")


def add_new_version(prompt_id: str):
    """Add a new version to demonstrate version history."""
    registry = PromptRegistry()

    print(f"\n[VERSIONING] Adding new version to '{prompt_id}'...")
    registry.update_prompt(
        prompt_id=prompt_id,
        system_instructions=(
            "You are an UPGRADED billing support assistant for a telecom company. "
            "Always be polite, concise, and empathetic. "
            "Never share sensitive payment details in plain text. "
            "NEW: Offer proactive solutions before customer asks. "
            "If you cannot resolve the issue, escalate to a human agent immediately."
        ),
        template=(
            "Customer has a query about: {issue_type}\n"
            "Account ID: {account_id}\n"
            "Last payment date: {last_payment_date}\n"
            "Customer tier: {customer_tier}\n\n"
            "Provide a personalized resolution based on customer tier."
        ),
        change_note="Added customer tier personalization + proactive solutions"
    )


def rollback_demo(prompt_id: str, target_version: int):
    """Demonstrate rollback to a previous version."""
    registry = PromptRegistry()

    print(f"\n{'=' * 65}")
    print(f"  ROLLBACK DEMO")
    print(f"{'=' * 65}")
    print(f"  Prompt   : {prompt_id}")
    print(f"  Rollback to: v{target_version}")

    registry.rollback(prompt_id=prompt_id, target_version=target_version)

    # Confirm rollback via API
    print(f"\n  [CONFIRMATION] Verifying rollback via registry...")
    prompt = registry.get_prompt(prompt_id)
    active_version = prompt["current_version"]
    active_content = prompt["versions"][str(active_version)]

    print(f"  Active Version  : v{active_version}")
    print(f"  Change Note     : {active_content['change_note']}")
    print(f"  Content matches v{target_version}: ", end="")

    original = registry.get_version_history(prompt_id)
    original_content = next(v for v in original if v["version"] == target_version)

    if (active_content["system_instructions"] ==
            original_content["system_instructions"]):
        print("YES ✓ - Rollback confirmed!")
    else:
        print("NO ✗ - Something went wrong")


if __name__ == "__main__":
    prompt_id = "dfcx_billing_billing_payment_query_dev"

    # Step 1: Show initial version history (v1 only)
    print("\n>>> STEP 1: Initial version history")
    show_version_history(prompt_id)

    # Step 2: Add v2
    print("\n>>> STEP 2: Adding v2 (upgraded prompt)")
    add_new_version(prompt_id)

    # Step 3: Add v3
    print("\n>>> STEP 3: Adding v3 (another update)")
    registry = PromptRegistry()
    registry.update_prompt(
        prompt_id=prompt_id,
        system_instructions=(
            "You are a billing support assistant. "
            "This is version 3 - experimental changes. "
            "Handle all billing queries with extreme caution."
        ),
        template=(
            "Query: {issue_type}\n"
            "Account: {account_id}\n"
            "Resolve carefully."
        ),
        change_note="Experimental v3 - caution mode"
    )

    # Step 4: Show full history (v1, v2, v3)
    print("\n>>> STEP 4: Full version history (v1, v2, v3)")
    show_version_history(prompt_id)

    # Step 5: Rollback to v1
    print("\n>>> STEP 5: Rolling back to v1")
    rollback_demo(prompt_id, target_version=1)

    # Step 6: Show history after rollback (v1,v2,v3,v4=rollback)
    print("\n>>> STEP 6: Version history after rollback")
    show_version_history(prompt_id)