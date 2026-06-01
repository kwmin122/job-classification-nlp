from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import re
from typing import Protocol


TECH_NORMALIZE = {
    r"\bpython\b|파이썬": "Python",
    r"\bpytorch\b|\bpyTorch\b|파이토치": "PyTorch",
    r"\btensorflow\b|\btensorFlow\b|텐서플로|텐서플로우": "TensorFlow",
    r"\breact\.js\b|\breactjs\b|\breact\b": "React",
    r"\bnext\.js\b|\bnextjs\b|\bnext js\b": "Nextjs",
    r"\bvue\.js\b|\bvuejs\b|\bvue\b": "Vue",
    r"\btypescript\b": "TypeScript",
    r"\bjavascript\b": "JavaScript",
    r"\bspring boot\b|\bspringboot\b|\bspring\b": "SpringBoot",
    r"\bjava\b|\b자바\b": "Java",
    r"\bkotlin\b|\b코틀린\b": "Kotlin",
    r"\bnode\.js\b|\bnodejs\b|\bnode js\b": "Nodejs",
    r"\bdocker\b|\b도커\b": "Docker",
    r"\bkubernetes\b|\bk8s\b|\b쿠버네티스\b": "Kubernetes",
    r"\baws\b|\bamazon web services\b": "AWS",
    r"\bgcp\b|\bgoogle cloud\b": "GCP",
    r"\bazure\b|\bmicrosoft azure\b": "Azure",
    r"\bmysql\b|\bpostgresql\b|\bpostgres\b|\bsql\b": "SQL",
    r"\bmongodb\b|\bmongo\b": "MongoDB",
    r"\bredis\b": "Redis",
    r"\bgithub\b|\bgitlab\b|\bgit\b": "Git",
    r"\bci/cd\b|\bcicd\b|\bci cd\b": "CICD",
    r"\bmlops\b|\bml ops\b": "MLOps",
    r"\bllm\b|\blarge language model\b|\b대규모 언어 모델\b": "LLM",
    r"\brag\b|\bretrieval augmented generation\b": "RAG",
    r"\bnlp\b|\b자연어 처리\b|\b자연어처리\b": "NLP",
    r"\bcomputer vision\b|\b컴퓨터 비전\b|\b컴퓨터비전\b": "ComputerVision",
    r"\btableau\b|\b태블로\b": "Tableau",
    r"\brest api\b|\brestful api\b|\brestful\b": "RESTAPI",
    r"\bpandas\b|\b판다스\b": "Pandas",
    r"\bscikit-learn\b|\bsklearn\b": "ScikitLearn",
    r"\bairflow\b": "Airflow",
    r"\bpower bi\b|\bpowerbi\b|\bpbi\b": "PowerBI",
    r"\bspark\b|\b스파크\b": "Spark",
    r"\bhive\b": "Hive",
    r"\bhadoop\b": "Hadoop",
    r"\bab테스트\b|\ba/b test\b|\ba/b\b|\babt\b": "ABTest",
    r"\blooker\b": "Looker",
    r"\bmetabase\b": "Metabase",
    r"\bsuperset\b": "Superset",
    r"\b통계\b": "통계분석",
    r"\b마케팅\b": "마케팅분석",
    r"\b지표\b": "데이터지표",
    r"\b데이터\s*파이프라인\b": "데이터파이프라인",
    r"\b데이터\s*웨어하우스\b|\bdwh\b|\bdw\b": "데이터웨어하우스",
    r"\b대시보드\b": "대시보드시각화",
    r"\b시각화\b": "데이터시각화",
}

STOPWORDS = {
    "있",
    "수",
    "및",
    "등",
    "이",
    "가",
    "을",
    "를",
    "은",
    "는",
    "에",
    "의",
    "로",
    "으로",
    "와",
    "과",
    "도",
    "만",
    "에서",
    "하다",
    "하는",
    "하고",
    "합니다",
    "있습니다",
    "있으며",
    "통해",
    "위해",
    "위한",
    "대한",
    "관련",
    "기반",
    "분",
    "경험",
    "능력",
    "역량",
    "업무",
    "개발",
    "서비스",
    "시스템",
    "환경",
    "이상",
    "이하",
    "담당",
    "운영",
    "구축",
    "설계",
    "분야",
    "직무",
    "지원",
    "채용",
    "신입",
    "경력",
    "인턴",
    "우대",
    "필수",
    "자격",
    "요건",
    "사항",
    "내용",
    "방법",
}


class OktLike(Protocol):
    def pos(self, phrase: str, norm: bool = ..., stem: bool = ...) -> list[tuple[str, str]]:
        ...


def _configure_java_home() -> None:
    if os.environ.get("JAVA_HOME"):
        return

    brewed_home = Path("/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home")
    if brewed_home.exists():
        os.environ["JAVA_HOME"] = str(brewed_home)
        os.environ["PATH"] = f"{brewed_home / 'bin'}:{os.environ.get('PATH', '')}"


@lru_cache(maxsize=1)
def get_okt():
    _configure_java_home()
    from konlpy.tag import Okt

    return Okt()


def normalize_tech(text: str) -> str:
    for pattern, replacement in TECH_NORMALIZE.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def preprocess_for_job_classifier(text: str, okt: OktLike | None = None) -> str:
    if not isinstance(text, str):
        return ""

    parser = okt or get_okt()
    normalized = normalize_tech(text)
    tokens = parser.pos(normalized, norm=True, stem=True)
    result = []
    for word, pos in tokens:
        if pos in ("Noun", "Alpha", "Foreign") and word not in STOPWORDS and len(word) > 1:
            result.append(word)
    return " ".join(result)
