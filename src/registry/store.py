# src/registry/store.py
# Core Prompt Registry - Local simulation of Vertex AI Prompt Management
# Handles: CREATE, READ, UPDATE, DELETE, VERSION HISTORY, ROLLBACK

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
import config


class PromptRegistry:
    """
    Local registry that simulates Vertex AI Prompt Management.
    All prompts are stored in a single JSON file acting as the registry.
    """

    def __init__(self):
        self.registry_file = config.REGISTRY_FILE
        self._ensure_registry_exists()

    def _ensure_registry_exists(self):
        """Create empty registry file if it does not exist."""
        if not self.registry_file.exists():
            self._save({"prompts": {}})

    def _load(self) -> dict:
        """Load registry from JSON file."""
        with open(self.registry_file, "r") as f:
            return json.load(f)

    def _save(self, data: dict):
        """Save registry to JSON file with pretty formatting."""
        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _generate_prompt_id(
        self, name: str, domain: str, agent_type: str, environment: str = ""
    ) -> str:
        """
        Generate a deterministic, human-readable prompt ID.
        Format: {agent_type}_{domain}_{name_slug}_{environment}
        Example: dfcx_billing_payment_query_dev
        """
        name_slug = name.lower().replace(" ", "_")[:30]
        if environment:
            return f"{agent_type}_{domain}_{name_slug}_{environment}"
        return f"{agent_type}_{domain}_{name_slug}"

    def _timestamp(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"

    def _validate(self, domain: str, agent_type: str, environment: str):
        """Validate domain, agent_type, and environment against allowed values."""
        errors = []
        if domain not in config.DOMAINS:
            errors.append(f"Invalid domain '{domain}'. Allowed: {config.DOMAINS}")
        if agent_type not in config.AGENT_TYPES:
            errors.append(f"Invalid agent_type '{agent_type}'. Allowed: {config.AGENT_TYPES}")
        if environment not in config.ENVIRONMENTS:
            errors.append(f"Invalid environment '{environment}'. Allowed: {config.ENVIRONMENTS}")
        if errors:
            raise ValueError("\n".join(errors))

    def create_prompt(
        self,
        name: str,
        domain: str,
        agent_type: str,
        environment: str,
        system_instructions: str,
        template: str,
        model_parameters: Optional[dict] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Create a new prompt in the registry."""
        self._validate(domain, agent_type, environment)

        prompt_id = self._generate_prompt_id(name, domain, agent_type, environment)

        data = self._load()

        if prompt_id in data["prompts"]:
            raise ValueError(
                f"Prompt '{prompt_id}' already exists. "
                f"Use update_prompt() to add a new version."
            )

        now = self._timestamp()
        prompt = {
            "prompt_id":        prompt_id,
            "name":             name,
            "domain":           domain,
            "agent_type":       agent_type,
            "environment":      environment,
            "current_version":  config.INITIAL_VERSION,
            "created_at":       now,
            "updated_at":       now,
            "model_parameters": model_parameters or config.DEFAULT_MODEL_PARAMS,
            "metadata":         metadata or {},
            "versions": {
                str(config.INITIAL_VERSION): {
                    "version":             config.INITIAL_VERSION,
                    "system_instructions": system_instructions,
                    "template":            template,
                    "created_at":          now,
                    "created_by":          config.OPERATOR,
                    "change_note":         "Initial version"
                }
            }
        }

        data["prompts"][prompt_id] = prompt
        self._save(data)

        print(f"[CREATED] Prompt '{prompt_id}' (v{config.INITIAL_VERSION}) saved.")
        return prompt

    def get_prompt(self, prompt_id: str) -> dict:
        """Retrieve a prompt by its ID."""
        data = self._load()
        if prompt_id not in data["prompts"]:
            raise KeyError(f"Prompt '{prompt_id}' not found in registry.")

        prompt = data["prompts"][prompt_id]
        current_v = str(prompt["current_version"])
        result = {**prompt, **prompt["versions"][current_v]}
        return result

    def list_prompts(
        self,
        domain: Optional[str] = None,
        environment: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> list:
        """List prompts with optional filters."""
        data = self._load()
        results = []

        for prompt_id, prompt in data["prompts"].items():
            if domain and prompt["domain"] != domain:
                continue
            if environment and prompt["environment"] != environment:
                continue
            if agent_type and prompt["agent_type"] != agent_type:
                continue
            results.append(prompt)

        return results

    def update_prompt(
        self,
        prompt_id: str,
        system_instructions: str,
        template: str,
        change_note: str = "Updated version",
        model_parameters: Optional[dict] = None
    ) -> dict:
        """Add a new version to an existing prompt. Never overwrites old versions."""
        data = self._load()

        if prompt_id not in data["prompts"]:
            raise KeyError(f"Prompt '{prompt_id}' not found.")

        prompt = data["prompts"][prompt_id]
        new_version = prompt["current_version"] + 1
        now = self._timestamp()

        prompt["versions"][str(new_version)] = {
            "version":             new_version,
            "system_instructions": system_instructions,
            "template":            template,
            "created_at":          now,
            "created_by":          config.OPERATOR,
            "change_note":         change_note
        }

        prompt["current_version"] = new_version
        prompt["updated_at"] = now

        if model_parameters:
            prompt["model_parameters"] = model_parameters

        self._save(data)
        print(f"[UPDATED] Prompt '{prompt_id}' → v{new_version}")
        return prompt

    def get_version_history(self, prompt_id: str) -> list:
        """Retrieve full version history for a prompt."""
        data = self._load()
        if prompt_id not in data["prompts"]:
            raise KeyError(f"Prompt '{prompt_id}' not found.")

        versions = data["prompts"][prompt_id]["versions"]
        history = sorted(versions.values(), key=lambda x: x["version"])
        return history

    def rollback(self, prompt_id: str, target_version: int) -> dict:
        """
        Rollback a prompt to a previous version.
        Creates a NEW version with old content - audit trail preserved.
        """
        data = self._load()
        if prompt_id not in data["prompts"]:
            raise KeyError(f"Prompt '{prompt_id}' not found.")

        prompt = data["prompts"][prompt_id]
        versions = prompt["versions"]

        if str(target_version) not in versions:
            available = list(versions.keys())
            raise ValueError(
                f"Version {target_version} not found. "
                f"Available versions: {available}"
            )

        target_content = versions[str(target_version)]
        new_version = prompt["current_version"] + 1
        now = self._timestamp()

        prompt["versions"][str(new_version)] = {
            "version":             new_version,
            "system_instructions": target_content["system_instructions"],
            "template":            target_content["template"],
            "created_at":          now,
            "created_by":          config.OPERATOR,
            "change_note":         f"Rollback to v{target_version}"
        }

        prompt["current_version"] = new_version
        prompt["updated_at"] = now

        self._save(data)
        print(
            f"[ROLLBACK] Prompt '{prompt_id}' "
            f"rolled back to v{target_version} content → now active as v{new_version}"
        )
        return prompt