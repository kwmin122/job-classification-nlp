from __future__ import annotations

from dataclasses import dataclass

from app.services.resource_loader import load_resources
from app.services.retriever import TfidfRetriever
from app.services.scorer import difficulty_match, score_resource


@dataclass(frozen=True)
class BenchmarkCase:
    predicted_job: str
    skill: str
    difficulty: str
    query: str


BENCHMARKS = [
    BenchmarkCase("백엔드 개발자", "Docker", "입문", "백엔드 Docker 컨테이너 배포 입문"),
    BenchmarkCase("백엔드 개발자", "AWS", "기초", "백엔드 AWS 클라우드 배포 학습"),
    BenchmarkCase("프론트엔드 개발자", "React", "기초", "React 프론트엔드 컴포넌트 상태관리"),
    BenchmarkCase("프론트엔드 개발자", "TypeScript", "입문", "TypeScript JavaScript 타입 안정성"),
    BenchmarkCase("데이터 분석가", "SQL", "입문", "데이터 분석 SQL 쿼리 집계"),
    BenchmarkCase("데이터 분석가", "A/B 테스트", "기초", "A/B 테스트 통계 가설검정"),
    BenchmarkCase("AI/ML 엔지니어", "PyTorch", "기초", "PyTorch 딥러닝 모델 학습"),
    BenchmarkCase("AI/ML 엔지니어", "RAG", "실무", "LLM RAG 검색 증강 생성 파이프라인"),
]


def main() -> None:
    resources = load_resources()
    retriever = TfidfRetriever(resources)
    hit_count = 0
    precision_total = 0.0
    difficulty_total = 0.0

    for case in BENCHMARKS:
        candidates = retriever.search(case.query, limit=8)
        scored = [
            score_resource(
                resource=resource,
                semantic_similarity=similarity,
                skill=case.skill,
                predicted_job=case.predicted_job,
                user_difficulty=case.difficulty,
            )
            for resource, similarity in candidates
        ]
        top3 = sorted(scored, key=lambda item: item.recommend_score, reverse=True)[:3]
        skill_matches = [item for item in top3 if item.skill_match > 0]
        difficulty_matches = [
            item for item in top3 if difficulty_match(case.difficulty, item.resource) >= 0.5
        ]

        hit_count += 1 if skill_matches else 0
        precision_total += len(skill_matches) / 3
        difficulty_total += len(difficulty_matches) / 3

    case_count = len(BENCHMARKS)
    print(f"case_count={case_count}")
    print(f"hit_at_3={hit_count / case_count:.3f}")
    print(f"precision_at_3={precision_total / case_count:.3f}")
    print(f"difficulty_match_rate={difficulty_total / case_count:.3f}")


if __name__ == "__main__":
    main()
