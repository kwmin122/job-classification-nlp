from __future__ import annotations

import unittest

import numpy as np

from app.services.c_part import pipeline


SKILL_INDEX = {
    "spring boot": 0,
    "docker": 1,
    "aws": 2,
    "kubernetes": 3,
    "junit": 4,
}


def fake_embedding(text: str) -> np.ndarray:
    vector = np.zeros(len(SKILL_INDEX), dtype=float)
    lowered = text.lower()
    for token, index in SKILL_INDEX.items():
        if token in lowered:
            vector[index] = 1.0
    if not vector.any():
        vector[-1] = 0.1
    return vector


class CPartPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_get_embedding = pipeline.get_embedding
        pipeline.get_embedding = fake_embedding

    def tearDown(self) -> None:
        pipeline.get_embedding = self.original_get_embedding

    def test_long_text_loads_as_text_not_path(self) -> None:
        text = "채용공고 본문입니다. " * 500
        self.assertEqual(pipeline.load_text(text), text)

    def test_fit_score_counts_partial_as_half(self) -> None:
        """
        필수 Docker(coverage=85), 우대 AWS(coverage=50) →
        fit_score = 85 × 0.7 + 50 × 0.3 = 59.5 + 15.0 = 74.5 → 75
        """
        from app.services.c_part.pipeline import _compute_fit_score
        required = ["Docker", "AWS"]
        coverage_map = {"Docker": 85.0, "AWS": 50.0}
        importance_map = {"Docker": "필수", "AWS": "우대"}
        score = _compute_fit_score(required, coverage_map, importance_map)
        self.assertAlmostEqual(score, 75, delta=2)

    def test_outputs_owned_partial_and_gaps_without_overlap(self) -> None:
        result = pipeline.run_c_part_analysis(
            b_predicted_job="backend",
            jd_input=(
                "Spring Boot 개발 경험이 필수입니다. "
                "Docker 운영 경험이 필수입니다. "
                "AWS 배포 경험이 있으면 우대합니다."
            ),
            candidate_input=(
                "Spring Boot 기반 REST API를 설계하고 구현했습니다. "
                "AWS EC2를 간단히 사용해 본 경험이 있습니다. "
                "Docker는 들어본 적 있습니다."
            ),
            threshold=1.1,
        )
        self.assertEqual(result["status"], "success")
        owned = {item["skill"] for item in result["owned_skills"]}
        partial = {item["skill"] for item in result["partial_skills"]}
        gaps = {item["skill"] for item in result["skill_gaps"]}
        # coverage 기반 분류: 세 목록이 서로 겹치지 않으면 충분
        self.assertFalse(owned & partial)
        self.assertFalse(owned & gaps)
        self.assertFalse(partial & gaps)

    def test_extract_required_skills_no_overextraction(self) -> None:
        """JD에 명시되지 않은 스킬이 required_skills에 포함되지 않아야 한다."""
        from app.services.c_part import pipeline as _pl
        from app.services.c_part.pipeline import (
            extract_required_skills,
            split_sentences,
        )

        # 실제 임베딩 모델이 필요한 테스트 — fake embedding을 잠시 복원
        _pl.get_embedding = self.original_get_embedding
        get_embedding = self.original_get_embedding

        jd_text = (
            "Spring Boot 기반 REST API 개발 경험 필수.\n"
            "MySQL 데이터 모델링 및 쿼리 최적화.\n"
            "Docker 컨테이너 배포 경험 필요.\n"
            "AWS 클라우드 운영. CI/CD 파이프라인 구축."
        )
        jd_sentences = split_sentences(jd_text)
        jd_vectors = [get_embedding(s) for s in jd_sentences]

        result = extract_required_skills("backend", jd_sentences, jd_vectors)
        skill_names = [r["skill"] for r in result]

        # JD에 명시된 기술은 포함
        assert "Spring Boot" in skill_names, f"Spring Boot 누락: {skill_names}"
        assert "REST API" in skill_names, f"REST API 누락: {skill_names}"
        assert "MySQL" in skill_names, f"MySQL 누락: {skill_names}"
        assert "Docker" in skill_names, f"Docker 누락: {skill_names}"

        # JD에 없는 기술은 포함 불가
        assert "Java" not in skill_names, f"Java 과다 추출: {skill_names}"
        assert "Kotlin" not in skill_names, f"Kotlin 과다 추출: {skill_names}"
        assert "OpenAPI" not in skill_names, f"OpenAPI 과다 추출: {skill_names}"
        assert "PostgreSQL" not in skill_names, f"PostgreSQL 과다 추출: {skill_names}"
        assert "Node.js" not in skill_names, f"Node.js 과다 추출: {skill_names}"
        assert "JUnit" not in skill_names, f"JUnit 과다 추출: {skill_names}"

    def test_extract_required_skills_korean_aliases(self) -> None:
        """한국어 기술명 JD에서 정규화된 영문명으로 추출되어야 한다."""
        from app.services.c_part import pipeline as _pl
        from app.services.c_part.pipeline import (
            extract_required_skills,
            split_sentences,
        )

        # 실제 임베딩 모델이 필요한 테스트 — fake embedding을 잠시 복원
        _pl.get_embedding = self.original_get_embedding
        get_embedding = self.original_get_embedding

        jd_text = (
            "스프링 부트 기반 백엔드 개발 경험 3년 이상 필수.\n"
            "도커를 활용한 컨테이너 배포 경험.\n"
            "쿠버네티스 운영 경험 우대."
        )
        jd_sentences = split_sentences(jd_text)
        jd_vectors = [get_embedding(s) for s in jd_sentences]

        result = extract_required_skills("backend", jd_sentences, jd_vectors)
        skill_names = [r["skill"] for r in result]

        assert "Spring Boot" in skill_names, (
            f"'스프링 부트' → 'Spring Boot' alias 매칭 실패: {skill_names}"
        )
        assert "Docker" in skill_names, (
            f"'도커' → 'Docker' alias 매칭 실패: {skill_names}"
        )
        assert "Kubernetes" in skill_names, (
            f"'쿠버네티스' → 'Kubernetes' alias 매칭 실패: {skill_names}"
        )

    def test_keyword_hit_word_boundary_no_false_positive(self) -> None:
        """Java/Git 등이 JavaScript/GitHub에서 잘못 매칭되지 않아야 한다."""
        from app.services.c_part.pipeline import _keyword_hit_any

        # word-boundary: 이전 substring 방식의 false positive 케이스
        assert not _keyword_hit_any("Java", "JavaScript TypeScript 개발 경험"), \
            "Java must not match inside JavaScript"
        assert not _keyword_hit_any("Git", "GitHub Actions, GitLab CI/CD 사용"), \
            "Git must not match inside GitHub/GitLab"

        # 정상 매칭: 단어 경계에서 정확히 있는 경우
        assert _keyword_hit_any("Java", "Java와 Spring Boot 기반 REST API 개발"), \
            "Java exact match must pass"
        assert _keyword_hit_any("Git", "Git, SVN 버전 관리 경험 보유"), \
            "Git exact match must pass"

    def test_coverage_boundary_39_is_missing(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(39.9)[0], "missing")

    def test_coverage_boundary_40_is_partial(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(40.0)[0], "partial")

    def test_coverage_boundary_69_is_partial(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(69.9)[0], "partial")

    def test_coverage_boundary_70_is_owned(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(70.0)[0], "owned")

    def test_exp_bonus_caps_at_100(self) -> None:
        from app.services.c_part.pipeline import _compute_coverage, COV_STRONG
        cov = _compute_coverage(COV_STRONG + 0.1, has_exp_verb=True)
        self.assertLessEqual(cov, 100.0)

    def test_zero_sim_gives_zero_coverage(self) -> None:
        from app.services.c_part.pipeline import _compute_coverage
        cov = _compute_coverage(0.0)
        self.assertEqual(cov, 0.0)

    def test_compute_coverage_monotone(self) -> None:
        """sim 증가 → coverage 비감소."""
        from app.services.c_part.pipeline import _compute_coverage
        sims = [0.0, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
        covs = [_compute_coverage(s) for s in sims]
        for i in range(len(covs) - 1):
            self.assertLessEqual(covs[i], covs[i + 1])


class TestJdCandSimRegressionUnit(unittest.TestCase):
    """
    회귀 테스트: jd_cand_sim false positive 버그.

    sim = max(jd_cand_sim, skill_sim) 를 sim = skill_sim 으로 교체한 수정을
    구조적으로 고정합니다. fake_embedding을 써서 결정론적입니다.

    시나리오:
      JD 문장: "Python AI 프로그래밍 필수" → 벡터 [1, 1] (python=1, ai_general=1)
      지원자:  "AI 기술 학습 중" →            벡터 [0, 1] (ai_general만 있음)
      스킬:    "Python"         →            벡터 [1, 0]

      jd_cand_sim = cosine([1,1]/√2, [0,1]) ≈ 0.707   ← 높음 (같은 AI 도메인)
      skill_sim   = cosine([1,0],    [0,1]) = 0         ← 낮음

      구 코드: sim=0.707 → coverage 100% → Python owned  (버그)
      수정 후: sim=0     → coverage 0%   → Python missing (정상)
    """

    def setUp(self) -> None:
        self.original_embed = pipeline.get_embedding
        pipeline.get_embedding = self._fake_embed

    def tearDown(self) -> None:
        pipeline.get_embedding = self.original_embed

    @staticmethod
    def _fake_embed(text: str) -> np.ndarray:
        v = np.zeros(2)
        t = text.lower()
        if "python" in t:
            v[0] = 1.0
        if any(w in t for w in ("ai", "인공지능", "machine", "ml", "llm")):
            v[1] = 1.0
        norm = np.linalg.norm(v)
        return v / norm if norm > 1e-9 else np.array([0.0, 1.0])

    def test_same_domain_candidate_does_not_own_unmentioned_skill(self) -> None:
        """
        지원자가 'AI 기술'만 언급했을 때 Python은 missing이어야 한다.
        jd_cand_sim 이 쓰이면 0.707로 owned가 되는 버그가 재발한다.
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input="Python AI 프로그래밍 경험이 필수입니다.",
            candidate_input="AI 기술을 학습 중입니다. 관련 분야에 관심이 있습니다.",
            explicit_required_skills=["Python"],
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        missing = {x["skill"] for x in result["skill_gaps"]}
        # 핵심 회귀 어서션
        self.assertNotIn("Python", owned, "Python이 owned — jd_cand_sim 버그 재발")
        self.assertIn("Python", missing, "Python이 missing에 없음")

    def test_concordant_candidate_still_owns_skill_after_fix(self) -> None:
        """
        지원자가 실제로 Python을 언급하면 수정 후에도 owned이어야 한다.
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input="Python AI 프로그래밍 경험이 필수입니다.",
            candidate_input="Python으로 AI 모델을 개발했습니다.",
            explicit_required_skills=["Python"],
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        self.assertIn("Python", owned, "Python이 owned가 아님 — 수정이 과도하게 제한함")


class TestSkillMatchingIntegration(unittest.TestCase):
    """
    스킬 매칭 통합 테스트 — 실제 임베딩 모델 사용, 네트워크 없음.

    모든 케이스에서 예측을 먼저 작성하고 어서션으로 검증합니다.
    """

    # ── 공통 픽스처 ─────────────────────────────────────────────────────
    AI_JD = (
        "AI/ML 엔지니어 채용. "
        "Python 등 AI 프로그래밍 숙련자 필수. "
        "LangChain, RAG 파이프라인 구축 경험 필수. "
        "MLOps 환경에서 Docker 기반 모델 배포 경험 우대. "
        "AI Agent 설계 및 운영 경험 우대."
    )
    FRONTEND_JD = (
        "프론트엔드 개발자 채용. "
        "React와 TypeScript 경험 필수. "
        "Next.js SSR/SSG 구현 경험 우대. "
        "CSS 반응형 UI 설계 경험 필수."
    )

    AI_RESUME = (
        "Python으로 LLM 기반 AI 서비스를 개발했습니다. "
        "LangChain 프레임워크로 RAG 파이프라인을 구축했습니다. "
        "MLOps 워크플로우를 설계하고 Docker 컨테이너로 모델을 배포했습니다. "
        "AI Agent 시스템을 설계하고 운영했습니다."
    )
    FRONTEND_RESUME = (
        "React와 TypeScript로 SPA를 개발했습니다. "
        "Next.js SSR로 성능을 최적화했습니다. "
        "CSS-in-JS로 반응형 UI를 구현했습니다."
    )
    FRONTEND_LETTER = (  # 유저가 보고한 실제 버그 케이스
        "저는 AI 기술과 프론트엔드 개발을 함께 학습하며, "
        "사용자가 쉽게 활용할 수 있는 웹 서비스를 만드는 개발자가 되고자 준비해왔습니다. "
        "HTML, CSS, JavaScript, React를 공부했고, "
        "API 연동과 반응형 화면 구성, 기본적인 UI/UX 설계에 관심을 가지고 프로젝트를 진행했습니다."
    )
    BACKEND_RESUME = (
        "Java와 Spring Boot로 REST API를 설계하고 구현했습니다. "
        "MySQL과 Redis를 활용한 백엔드 서비스를 개발했습니다. "
        "Docker로 컨테이너 환경을 구성했습니다."
    )

    AI_EXPLICIT = ["Python", "LangChain", "MLOps", "Docker", "AI Agent", "RAG"]
    FRONTEND_EXPLICIT = ["React", "TypeScript", "Next.js", "CSS"]

    # ── text-path 케이스 (structured_skills=[], explicit=None) ──────────

    def test_discordant_frontend_letter_vs_ai_job_text_path(self) -> None:
        """
        예측: 프론트엔드 자소서 + AI 공고 → Python∉owned, Docker∉owned, fit<30
        이 케이스가 100점을 반환했던 원래 버그.
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input=self.AI_JD,
            candidate_input=self.FRONTEND_LETTER,
            explicit_required_skills=None,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertNotIn("Python", owned,  "Python owned — 버그 재발 가능성")
        self.assertNotIn("LangChain", owned, "LangChain owned — 버그 재발 가능성")
        self.assertNotIn("Docker", owned,  "Docker owned — 버그 재발 가능성")
        self.assertNotIn("MLOps", owned,   "MLOps owned — 버그 재발 가능성")
        self.assertLess(fit, 30, f"fit={fit} — 불일치 케이스인데 너무 높음")

    def test_concordant_ai_resume_vs_ai_job_text_path(self) -> None:
        """
        예측: AI 이력서 + AI 공고 → Python∈owned, LangChain∈owned, fit>70
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input=self.AI_JD,
            candidate_input=self.AI_RESUME,
            explicit_required_skills=None,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertIn("Python", owned,    "Python not owned — 일치 케이스에서 누락")
        self.assertIn("LangChain", owned, "LangChain not owned — 일치 케이스에서 누락")
        self.assertGreater(fit, 70, f"fit={fit} — 일치 케이스인데 너무 낮음")

    # ── explicit-path 케이스 (structured_skills 있음) ──────────────────

    def test_discordant_frontend_letter_vs_ai_job_explicit_path(self) -> None:
        """
        예측: 프론트엔드 자소서 + AI 공고(explicit) → Python∉owned, fit<30
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input=self.AI_JD,
            candidate_input=self.FRONTEND_LETTER,
            explicit_required_skills=self.AI_EXPLICIT,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertNotIn("Python", owned,   "Python owned — explicit 경로 오탐")
        self.assertNotIn("LangChain", owned, "LangChain owned — explicit 경로 오탐")
        self.assertLess(fit, 30, f"fit={fit} — explicit 불일치인데 너무 높음")

    def test_concordant_ai_resume_vs_ai_job_explicit_path(self) -> None:
        """
        예측: AI 이력서 + AI 공고(explicit) → Python∈owned, LangChain∈owned, fit>70
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input=self.AI_JD,
            candidate_input=self.AI_RESUME,
            explicit_required_skills=self.AI_EXPLICIT,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertIn("Python", owned,    "Python not owned — explicit 일치 케이스 누락")
        self.assertIn("LangChain", owned, "LangChain not owned — explicit 일치 케이스 누락")
        self.assertGreater(fit, 70, f"fit={fit} — explicit 일치인데 너무 낮음")

    def test_discordant_backend_resume_vs_ai_job_explicit_path(self) -> None:
        """
        예측: 백엔드 이력서 + AI 공고(explicit) → Docker∈owned, LangChain∉owned
        Docker는 명시적 언급 → owned. LangChain은 언급 없음 → missing.
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="ai",
            jd_input=self.AI_JD,
            candidate_input=self.BACKEND_RESUME,
            explicit_required_skills=self.AI_EXPLICIT,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}

        self.assertIn("Docker", owned,       "Docker not owned — 백엔드 이력서에 명시됨")
        self.assertNotIn("LangChain", owned, "LangChain owned — 백엔드 이력서에 없음")

    def test_concordant_frontend_resume_vs_frontend_job_explicit_path(self) -> None:
        """
        예측: 프론트 이력서 + 프론트 공고(explicit) → React∈owned, TypeScript∈owned, fit>70
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="frontend",
            jd_input=self.FRONTEND_JD,
            candidate_input=self.FRONTEND_RESUME,
            explicit_required_skills=self.FRONTEND_EXPLICIT,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertIn("React", owned,      "React not owned — 프론트 일치 케이스")
        self.assertIn("TypeScript", owned, "TypeScript not owned — 프론트 일치 케이스")
        self.assertGreater(fit, 70, f"fit={fit} — 프론트 일치인데 너무 낮음")

    def test_discordant_ai_resume_vs_frontend_job_explicit_path(self) -> None:
        """
        예측: AI 이력서 + 프론트 공고(explicit) → React∉owned, TypeScript∉owned, fit<20
        """
        result = pipeline.run_c_part_analysis(
            b_predicted_job="frontend",
            jd_input=self.FRONTEND_JD,
            candidate_input=self.AI_RESUME,
            explicit_required_skills=self.FRONTEND_EXPLICIT,
        )
        self.assertEqual(result["status"], "success")
        owned = {x["skill"] for x in result["owned_skills"]}
        fit = result["fit_score"]

        self.assertNotIn("React",      owned, "React owned — AI 이력서에 없음")
        self.assertNotIn("TypeScript", owned, "TypeScript owned — AI 이력서에 없음")
        self.assertLess(fit, 20, f"fit={fit} — 완전 불일치인데 너무 높음")


if __name__ == "__main__":
    unittest.main()
