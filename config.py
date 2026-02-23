# config.py
# Central configuration for Vertex AI Prompt Management PoC
# All project-wide settings are controlled from this single file

import os
from pathlib import Path

# ─── Project Paths ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "prompts"
DOCS_DIR = BASE_DIR / "docs"

# Auto-create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Environment Lifecycle ───────────────────────────────────────────────────
# Promotion order: dev → qa → staging → prod
# Migration can only happen in this sequence (no skipping allowed)
ENVIRONMENTS = ["dev", "qa", "staging", "prod"]

ENVIRONMENT_TRANSITIONS = {
    "dev":     "qa",
    "qa":      "staging",
    "staging": "prod",
    "prod":    None   # prod is the final stage, no further promotion
}

# ─── Business Domains ────────────────────────────────────────────────────────
# Each prompt must belong to exactly one domain
DOMAINS = [
    "billing",       # Payment, invoice, refund related prompts
    "tech_support",  # Technical troubleshooting prompts
    "account_mgmt",  # Account creation, update, deletion prompts
    "general",       # General purpose prompts
    "shared"         # Cross-cutting: safety guardrails, tone guidelines
]

# ─── Agent Types ─────────────────────────────────────────────────────────────
# Three source systems from which prompts are ingested
AGENT_TYPES = ["dfcx", "adk", "custom"]

# ─── Registry File ───────────────────────────────────────────────────────────
# This JSON file acts as our local prompt registry
# In real GCP: this maps to Vertex AI Prompt Management API
REGISTRY_FILE = DATA_DIR / "prompt_registry.json"

# Manifest file stores migration history
MANIFEST_FILE = DATA_DIR / "migration_manifest.json"

# ─── Operator Identity ───────────────────────────────────────────────────────
# Used in migration manifests to track who performed the migration
OPERATOR = os.getenv("OPERATOR_NAME", "pawan.malik")

# ─── Default Model Parameters ────────────────────────────────────────────────
# These are applied to prompts unless overridden at prompt level
DEFAULT_MODEL_PARAMS = {
    "model":            "gemini-1.5-pro",
    "temperature":      0.7,
    "max_output_tokens": 1024,
    "top_p":            0.9,
    "top_k":            40
}

# ─── Versioning ──────────────────────────────────────────────────────────────
INITIAL_VERSION = 1