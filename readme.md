# Vertex AI Prompt Management - PoC

## Overview
This PoC demonstrates centralized prompt storage, organization, 
and promotion across environments (dev → qa → staging → prod) 
simulating Vertex AI Prompt Management.

---

## Project Structure
```
vertex-prompt-poc/
├── config.py                         # Central configuration
├── main.py                           # Master entry point
├── src/
│   ├── ingestion/
│   │   ├── dfcx_ingestor.py         # Dialogflow CX prompt extractor
│   │   ├── adk_ingestor.py          # ADK agent prompt extractor
│   │   ├── custom_ingestor.py       # Custom agent prompt extractor
│   │   └── ingest_all.py            # Master ingestor
│   ├── registry/
│   │   └── store.py                 # Core prompt registry engine
│   ├── migration/
│   │   └── migrate.py               # Migration CLI
│   └── utils/
│       ├── filter.py                # Domain/environment filtering
│       └── versioning.py            # Version history + rollback
├── data/prompts/
│   ├── prompt_registry.json         # Central prompt registry (DB)
│   └── migration_manifest.json      # Migration audit trail
└── docs/
    └── README.md                    # This file
```

---

## Storage Schema

Every prompt stored in the registry has this structure:
```json
{
  "prompt_id": "dfcx_billing_billing_payment_query_dev",
  "name": "billing_payment_query",
  "domain": "billing",
  "agent_type": "dfcx",
  "environment": "dev",
  "current_version": 1,
  "created_at": "2026-02-23T12:00:00Z",
  "updated_at": "2026-02-23T12:00:00Z",
  "model_parameters": {
    "model": "gemini-1.5-pro",
    "temperature": 0.7,
    "max_output_tokens": 1024
  },
  "metadata": {
    "source_agent": "telecom-billing-agent-v2",
    "extracted_by": "dfcx_ingestor"
  },
  "versions": {
    "1": {
      "version": 1,
      "system_instructions": "You are a billing support assistant...",
      "template": "Customer has a query about: {issue_type}...",
      "created_at": "2026-02-23T12:00:00Z",
      "created_by": "pawan.malik",
      "change_note": "Initial version"
    }
  }
}
```

---

## Domain Taxonomy

| Domain | Description | Example Prompts |
|--------|-------------|-----------------|
| billing | Payment, invoice, refund queries | payment_query, refund_handler |
| tech_support | Technical troubleshooting | troubleshoot, device_reset |
| account_mgmt | Account CRUD operations | update_handler, verify_identity |
| general | General purpose | greeting, fallback |
| shared | Cross-cutting concerns | safety_guardrails, tone_guidelines |

> **shared** domain prompts apply to ALL agents regardless of domain.

---

## Environment Lifecycle
```
┌─────┐     ┌────┐     ┌─────────┐     ┌──────┐
│ DEV │────▶│ QA │────▶│ STAGING │────▶│ PROD │
└─────┘     └────┘     └─────────┘     └──────┘
  │            │             │              │
  └────────────┴─────────────┴──────────────┘
         No skipping allowed
         Each stage = new version
         Old versions never deleted
```

### Rules:
- Promotion only moves **forward** (dev→qa→staging→prod)
- **No skipping** allowed (dev cannot go directly to prod)
- Each migration creates a **new version** in target environment
- Source prompt remains **unchanged** after migration
- `prod` is the **final stage** — no further promotion

---

## Migration Workflow

### 1. Dry Run (verify before migrating)
```bash
python -c "
from src.migration.migrate import MigrationEngine
engine = MigrationEngine()
engine.migrate('dfcx_billing_billing_payment_query_dev', dry_run=True)
"
```

### 2. Actual Migration
```bash
python -c "
from src.migration.migrate import MigrationEngine
engine = MigrationEngine()
engine.migrate('dfcx_billing_billing_payment_query_dev', dry_run=False)
"
```

### 3. View Migration History
```bash
python -c "
from src.migration.migrate import MigrationEngine
MigrationEngine().show_manifest()
"
```

### Migration Manifest Format
```json
{
  "migrations": [
    {
      "migration_id": "mig_dfcx_billing_..._dev_to_qa_20260223",
      "source_prompt_id": "dfcx_billing_billing_payment_query_dev",
      "target_prompt_id": "dfcx_billing_billing_payment_query_qa",
      "source_env": "dev",
      "target_env": "qa",
      "source_version": 1,
      "target_version": 1,
      "operator": "pawan.malik",
      "timestamp": "2026-02-23T12:03:17Z",
      "status": "success"
    }
  ]
}
```

---

## Versioning & Rollback

### View Version History
```bash
python -c "
from src.utils.versioning import show_version_history
show_version_history('dfcx_billing_billing_payment_query_dev')
"
```

### Rollback to Previous Version
```bash
python -c "
from src.utils.versioning import rollback_demo
rollback_demo('dfcx_billing_billing_payment_query_dev', target_version=1)
"
```

> **Note:** Rollback creates a NEW version with old content.
> Audit trail is always preserved. Nothing is ever deleted.

---

## IAM Mapping (GCP Production)

| Role | Service Account | Permissions |
|------|----------------|-------------|
| Platform Admin | platform-admin@project.iam | Create, Read, Update, Migrate |
| Domain Team | billing-team@project.iam | Read (billing domain only) |
| CI/CD Pipeline | cicd-sa@project.iam | Migrate (dev→qa only) |
| Release Manager | release-mgr@project.iam | Migrate (qa→staging→prod) |
| Read Only | readonly-sa@project.iam | List, Get only |

---

## Quick Start
```bash
# 1. Setup
python -m venv venv
venv\Scripts\activate
pip install typer rich faker python-dateutil tabulate

# 2. Run full demo
python main.py --demo 

# 3. Individual commands
python src/ingestion/ingest_all.py       # Ingest all prompts
python src/utils/filter.py               # Test filtering
python src/migration/migrate.py          # Test migration
python src/utils/versioning.py           # Test versioning
```

---

## GCP Production Mapping

| Local (PoC) | GCP Production |
|-------------|----------------|
| prompt_registry.json | Vertex AI Prompt Management API |
| migration_manifest.json | Cloud Logging / BigQuery audit table |
| config.py environments | GCP Projects (dev/qa/staging/prod) |
| OPERATOR variable | Cloud Identity / IAM principal |
| store.py PromptRegistry | aiplatform.PromptManagement client |