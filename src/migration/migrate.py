# src/migration/migrate.py
# Migration CLI - promotes prompts across environments
# dev → qa → staging → prod (strict order, no skipping)
# Creates new prompt entries with environment suffix in ID
# Supports dry-run mode and generates migration manifest

import sys
import json
import copy
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

import config
from src.registry.store import PromptRegistry


class MigrationEngine:
    """
    Handles promotion of prompts from one environment to the next.
    
    Key design:
    - Each environment gets its OWN prompt entry with env suffix in ID
    - Example: dfcx_billing_payment_query_dev → dfcx_billing_payment_query_qa
    - Never overwrites - always creates new or adds version
    - Full audit trail via migration manifest
    """

    def __init__(self):
        self.registry = PromptRegistry()
        self.manifest_file = config.MANIFEST_FILE

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _load_manifest(self) -> dict:
        if self.manifest_file.exists():
            with open(self.manifest_file, "r") as f:
                return json.load(f)
        return {"migrations": []}

    def _save_manifest(self, manifest: dict):
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=str)

    def _timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _build_env_prompt_id(self, base_prompt_id: str, environment: str) -> str:
        """
        Build environment-specific prompt ID.
        Example: dfcx_billing_payment_query + qa 
              → dfcx_billing_payment_query_qa
        """
        # Remove existing env suffix if present
        for env in config.ENVIRONMENTS:
            if base_prompt_id.endswith(f"_{env}"):
                base_prompt_id = base_prompt_id[: -(len(env) + 1)]
                break
        return f"{base_prompt_id}_{environment}"

    def _get_base_prompt_id(self, prompt_id: str) -> str:
        """Strip environment suffix from prompt ID."""
        for env in config.ENVIRONMENTS:
            if prompt_id.endswith(f"_{env}"):
                return prompt_id[: -(len(env) + 1)]
        return prompt_id

    # ─── Core Migration ───────────────────────────────────────────────────────

    def migrate(self, prompt_id: str, dry_run: bool = False) -> dict:
        """
        Promote a prompt to the next environment.
        
        Args:
            prompt_id:  Source prompt ID (with or without env suffix)
            dry_run:    If True, simulate only - no actual changes
            
        Returns:
            Migration manifest entry dict
        """
        # Step 1: Load source prompt
        data = self.registry._load()
        all_ids = list(data["prompts"].keys())

        # Find the prompt (handle with/without env suffix)
        resolved_id = None
        if prompt_id in all_ids:
            resolved_id = prompt_id
        else:
            # Try matching base ID
            for pid in all_ids:
                if self._get_base_prompt_id(pid) == self._get_base_prompt_id(prompt_id):
                    resolved_id = pid
                    break

        if resolved_id is None:
            raise KeyError(f"Prompt '{prompt_id}' not found in registry.")

        source_prompt = self.registry.get_prompt(resolved_id)
        source_env = source_prompt["environment"]
        source_version = source_prompt["current_version"]
        version_content = source_prompt["versions"][str(source_version)]

        # Step 2: Get target environment
        target_env = config.ENVIRONMENT_TRANSITIONS.get(source_env)
        if target_env is None:
            raise ValueError(
                f"Prompt is already in 'prod'. Cannot promote further."
            )

        # Step 3: Build target prompt ID
        base_id = self._get_base_prompt_id(resolved_id)
        target_prompt_id = self._build_env_prompt_id(base_id, target_env)

        print(f"\n{'=' * 60}")
        print(f"  MIGRATION: {source_env.upper()} → {target_env.upper()}")
        print(f"{'=' * 60}")
        print(f"  Source Prompt ID : {resolved_id}")
        print(f"  Target Prompt ID : {target_prompt_id}")
        print(f"  Source Version   : v{source_version}")
        print(f"  Operator         : {config.OPERATOR}")
        print(f"  Dry Run          : {dry_run}")
        print(f"{'=' * 60}")

        # Step 4: Build manifest entry
        manifest_entry = {
            "migration_id":   (
                f"mig_{base_id}_{source_env}_to_{target_env}_"
                f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            ),
            "source_prompt_id":  resolved_id,
            "target_prompt_id":  target_prompt_id,
            "source_env":        source_env,
            "target_env":        target_env,
            "source_version":    source_version,
            "target_version":    None,
            "operator":          config.OPERATOR,
            "timestamp":         self._timestamp(),
            "dry_run":           dry_run,
            "status":            "pending"
        }

        # Step 5: Dry run - stop here
        if dry_run:
            print(f"\n  [DRY RUN] No changes made to registry.")
            print(f"  [DRY RUN] Would create '{target_prompt_id}' in '{target_env}'")
            manifest_entry["status"] = "dry_run"
            self._print_manifest(manifest_entry)
            return manifest_entry

        # Step 6: Check if target already exists
        existing_in_target = [
            p["prompt_id"]
            for p in self.registry.list_prompts(environment=target_env)
        ]

        if target_prompt_id in existing_in_target:
            # Add new version to existing target prompt
            print(f"\n  Prompt exists in '{target_env}' - adding new version...")
            updated = self.registry.update_prompt(
                prompt_id=target_prompt_id,
                system_instructions=version_content["system_instructions"],
                template=version_content["template"],
                change_note=f"Promoted from {source_env} v{source_version}"
            )
            target_version = updated["current_version"]
        else:
            # Create fresh prompt in target environment
            print(f"\n  Creating new prompt in '{target_env}'...")
            created = self.registry.create_prompt(
                name=source_prompt["name"],
                domain=source_prompt["domain"],
                agent_type=source_prompt["agent_type"],
                environment=target_env,
                system_instructions=version_content["system_instructions"],
                template=version_content["template"],
                model_parameters=copy.deepcopy(source_prompt["model_parameters"]),
                metadata={
                    **source_prompt.get("metadata", {}),
                    "promoted_from":         source_env,
                    "promoted_from_version": source_version,
                    "promoted_by":           config.OPERATOR
                }
            )
            target_version = created["current_version"]

        # Step 7: Finalize manifest
        manifest_entry["target_version"] = target_version
        manifest_entry["status"] = "success"

        manifest = self._load_manifest()
        manifest["migrations"].append(manifest_entry)
        self._save_manifest(manifest)

        print(f"\n  [SUCCESS] Migrated to '{target_env}' → {target_prompt_id} (v{target_version})")
        self._print_manifest(manifest_entry)
        return manifest_entry

    def _print_manifest(self, entry: dict):
        print(f"\n  --- MIGRATION MANIFEST ENTRY ---")
        print(f"  Migration ID  : {entry['migration_id']}")
        print(f"  Source        : {entry['source_prompt_id']} ({entry['source_env']} v{entry['source_version']})")
        print(f"  Target        : {entry['target_prompt_id']} ({entry['target_env']} v{entry.get('target_version', 'N/A')})")
        print(f"  Operator      : {entry['operator']}")
        print(f"  Timestamp     : {entry['timestamp']}")
        print(f"  Status        : {entry['status']}")
        print(f"  --------------------------------")

    def show_manifest(self):
        """Display full migration history."""
        manifest = self._load_manifest()
        migrations = manifest.get("migrations", [])

        if not migrations:
            print("\n[MANIFEST] No migrations recorded yet.")
            return

        print(f"\n{'=' * 60}")
        print(f"  MIGRATION HISTORY ({len(migrations)} migration(s))")
        print(f"{'=' * 60}")
        for i, entry in enumerate(migrations, 1):
            print(f"\n  [{i}] {entry.get('source_prompt_id','?')} → {entry.get('target_prompt_id','?')}")
            print(f"       {entry['source_env']} → {entry['target_env']}")
            print(f"       Status   : {entry['status']}")
            print(f"       Operator : {entry['operator']}")
            print(f"       Time     : {entry['timestamp']}")


if __name__ == "__main__":
    engine = MigrationEngine()

    # Demo 1: Dry Run
    print("\n>>> DEMO 1: Dry Run (no changes)")
    engine.migrate(
        prompt_id="dfcx_billing_billing_payment_query",
        dry_run=True
    )

    # Demo 2: Actual Migration dev → qa
    print("\n>>> DEMO 2: Actual Migration dev → qa")
    engine.migrate(
        prompt_id="dfcx_billing_billing_payment_query",
        dry_run=False
    )

    # Demo 3: Show manifest
    print("\n>>> DEMO 3: Migration History")
    engine.show_manifest()