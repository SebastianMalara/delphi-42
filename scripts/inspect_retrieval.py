from __future__ import annotations

import argparse
from pathlib import Path

from bot.oracle_bot import load_config
from core.oracle_service import OracleService
from core.retriever import KiwixRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Delphi-42 retrieval decisions.")
    parser.add_argument("--config", type=Path, required=True, help="Path to runtime config.")
    parser.add_argument("--question", required=True, help="Question to inspect.")
    args = parser.parse_args()

    config = load_config(args.config)
    retriever = KiwixRetriever(
        config.knowledge.zim_dir,
        config.knowledge.zim_allowlist,
        default_limit=config.knowledge.zim_search_limit,
        search_limit=config.knowledge.zim_search_limit,
    )

    service = OracleService(
        retriever=retriever,
        reply_config=config.reply,
    )
    decision = service.inspect_ask(args.question)

    print(f"question: {args.question}")
    print(f"anchor_terms: {', '.join(decision.anchor_terms) or '-'}")
    print(f"confidence: {decision.confidence.value}")
    print(f"source: {decision.source}")
    print(f"model_allowed: {'yes' if decision.should_use_model else 'no'}")
    print("candidates:")
    if not decision.candidates:
        print("- none")
    else:
        for chunk in decision.candidates:
            print(f"- title={chunk.title} source={chunk.source} score={chunk.matched_terms}")
    print("context:")
    if not decision.context:
        print("- none")
    else:
        for chunk in decision.context:
            print(
                f"- ordinal={chunk.ordinal} title={chunk.title} "
                f"source={chunk.source} snippet={chunk.snippet}"
            )


if __name__ == "__main__":
    main()
