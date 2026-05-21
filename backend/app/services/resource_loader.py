from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from app.schemas import Resource

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RESOURCE_PATH = DATA_DIR / "learning_resources.csv"


@lru_cache(maxsize=1)
def load_resources() -> list[Resource]:
    with RESOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    resources: list[Resource] = []
    for row in rows:
        row["reliability"] = int(row["reliability"])
        resources.append(Resource(**row))
    return resources


def resource_search_text(resource: Resource) -> str:
    return " ".join(
        [
            resource.job_group,
            resource.skill,
            resource.sub_skill,
            resource.title,
            resource.description,
            resource.reason,
        ]
    )
