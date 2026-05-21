from __future__ import annotations

import os
import sys

from app.services.embedding_retriever import DEFAULT_EMBEDDING_MODEL, EmbeddingRetriever
from app.services.resource_loader import load_resources


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required to build OpenAI embeddings.", file=sys.stderr)
        return 2

    resources = load_resources()
    retriever = EmbeddingRetriever(resources=resources, model=DEFAULT_EMBEDDING_MODEL)
    print(
        "built embeddings: "
        f"resources={len(resources)} "
        f"model={retriever.model} "
        f"dimensions={retriever.embedding_matrix.shape[1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
