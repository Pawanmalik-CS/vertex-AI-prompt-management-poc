# main.py
# Master entry point for Vertex AI Prompt Management PoC
# Fully Dynamic - No Hardcoded Prompt IDs

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.ingestion.ingest_all import ingest_all
from src.utils.filter import (
    list_all_prompts,
    filter_by_domain,
    filter_by_environment,
    filter_by_domain_and_environment
)
from src.migration.migrate import MigrationEngine
from src.utils.versioning import show_version_history, rollback_demo
from src.registry.store import PromptRegistry


def print_header(title: str):
    print(f"\n{'#' * 65}")
    print(f"#  {title}")
    print(f"{'#' * 65}")


def run_full_demo(prompt_id: str):
    """
    Full end-to-end demo of all PoC capabilities.
    Now takes prompt_id dynamically instead of hardcoding.
    """

    # ── AC1: Multi-source Ingestion ───────────────────────────────────────────
    print_header("AC1: MULTI-SOURCE PROMPT INGESTION (DFCX + ADK + CUSTOM)")
    ingest_all()

    # ── AC2: List all prompts with metadata ───────────────────────────────────
    print_header("AC2: ALL PROMPTS WITH FULL METADATA")
    list_all_prompts()

    # ── AC3: Domain & Environment filtering ───────────────────────────────────
    print_header("AC3: FILTERING DEMO")
    filter_by_environment("dev")

    # ── AC4: Migration dev → qa ───────────────────────────────────────────────
    print_header(f"AC4: MIGRATION CLI - DEV → QA (For ID: {prompt_id})")
    engine = MigrationEngine()

    print("\n--- Dry Run First ---")
    try:
        engine.migrate(prompt_id=prompt_id, dry_run=True)
        
        print("\n--- Actual Migration ---")
        engine.migrate(prompt_id=prompt_id, dry_run=False)
    except Exception as e:
        print(f"\n❌ MIGRATION ERROR: {e}")

    print("\n--- Migration History ---")
    engine.show_manifest()

    # ── AC5: Versioning & Rollback ────────────────────────────────────────────
    print_header(f"AC5: VERSIONING AND ROLLBACK (For ID: {prompt_id})")

    print("\n--- Current Version History ---")
    try:
        show_version_history(prompt_id)

        print("\n--- Adding New Version (Automated Update) ---")
        registry = PromptRegistry()
        registry.update_prompt(
            prompt_id=prompt_id,
            system_instructions="[UPDATED DEMO] You are an upgraded assistant with enhanced capabilities.",
            template="[UPDATED DEMO] Issue: {issue_type} | Account: {account_id}",
            change_note="Automated version update for Demo"
        )

        print("\n--- Version History After Update ---")
        show_version_history(prompt_id)

        print("\n--- Rollback to v1 ---")
        rollback_demo(prompt_id, target_version=1)

        print("\n--- Final Version History (Rollback as new version) ---")
        show_version_history(prompt_id)
        
    except Exception as e:
        print(f"\n❌ VERSIONING ERROR: {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print_header("POC COMPLETE - ALL ACCEPTANCE CRITERIA DEMONSTRATED")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vertex AI Prompt Management - Master CLI")
    
    parser.add_argument("--demo", action="store_true", help="Run the full automated demo")
    parser.add_argument("--ingest", action="store_true", help="Run all ingestors")
    parser.add_argument("--migrate", action="store_true", help="Migrate a prompt")
    parser.add_argument("--rollback", action="store_true", help="Rollback a prompt")
    parser.add_argument("--list", action="store_true", help="List all prompts")
    
    parser.add_argument("--id", type=str, help="Prompt ID")
    parser.add_argument("--version", type=int, help="Target version number")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for migration")
    parser.add_argument("--domain", type=str, help="Filter by domain (e.g., billing, tech_support)")
    parser.add_argument("--env", type=str, help="Filter by environment (e.g., dev, qa, prod)")

    args = parser.parse_args()

    # --- CLI Routing with Interactive Inputs ---
    
    if args.demo:
        demo_id = args.id
        if not demo_id:
            demo_id = input("\n⌨️  Please enter the Prompt ID for the Demo\n(e.g., custom_account_mgmt_account_update_handler_dev): > ")
        
        if demo_id.strip():
            run_full_demo(demo_id.strip())
        else:
            print("❌ Demo cancelled. No ID provided.")
            
    elif args.ingest:
        ingest_all()
        
    elif args.list:
        # if user give domain and env 
        if args.domain and args.env:
            print(f"\n🔍 Filtering by Domain: '{args.domain}' AND Environment: '{args.env}'")
            filter_by_domain_and_environment(args.domain, args.env)
            
        # only domain
        elif args.domain:
            print(f"\n🔍 Filtering by Domain: '{args.domain}'")
            filter_by_domain(args.domain)
            
        # only  environment 
        elif args.env:
            print(f"\n🔍 Filtering by Environment: '{args.env}'")
            filter_by_environment(args.env)
            
        # Nothing given
        else:
            list_all_prompts()
        
    elif args.migrate:
        mig_id = args.id
        if not mig_id:
            mig_id = input("\n⌨️  Please enter the Prompt ID to migrate: > ")
            
        if mig_id.strip():
            engine = MigrationEngine()
            engine.migrate(prompt_id=mig_id.strip(), dry_run=args.dry_run)
        else:
            print("❌ Migration cancelled. No ID provided.")
            
    elif args.rollback:
        rb_id = args.id
        rb_ver = args.version
        
        if not rb_id:
            rb_id = input("\n⌨️  Please enter the Prompt ID to rollback: > ")
        if not rb_ver and rb_id.strip():
            try:
                ver_input = input("\n⌨️  Please enter the target version number (e.g., 1): > ")
                rb_ver = int(ver_input.strip())
            except ValueError:
                print("❌ Error: Version must be a number.")
                rb_ver = None
                
        if rb_id.strip() and rb_ver:
            rollback_demo(rb_id.strip(), rb_ver)
        else:
            print("❌ Rollback cancelled. Missing valid ID or Version.")
            
    else:
        parser.print_help()