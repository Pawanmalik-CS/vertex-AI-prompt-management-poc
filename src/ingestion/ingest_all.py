# src/ingestion/ingest_all.py
# Master ingestor - runs all three ingestors in sequence
# Single entry point to populate the registry from all agent sources

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ingestion.dfcx_ingestor import ingest_dfcx_prompts
from src.ingestion.adk_ingestor import ingest_adk_prompts
from src.ingestion.custom_ingestor import ingest_custom_prompts


def ingest_all():
    print("=" * 60)
    print("  VERTEX AI PROMPT MANAGEMENT - BULK INGESTION")
    print("=" * 60)

    print("\n[1/3] Ingesting DFCX prompts...")
    dfcx_results = ingest_dfcx_prompts()

    print("\n[2/3] Ingesting ADK prompts...")
    adk_results = ingest_adk_prompts()

    print("\n[3/3] Ingesting Custom agent prompts...")
    custom_results = ingest_custom_prompts()

    total = len(dfcx_results) + len(adk_results) + len(custom_results)

    print("\n" + "=" * 60)
    print(f"  INGESTION COMPLETE - Total prompts ingested: {total}")
    print("=" * 60)


if __name__ == "__main__":
    ingest_all()