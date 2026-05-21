# JobKorea 기반 학습자료 DB 재선정 기준

Generated: 2026-05-20

## 목적

기존 학습자료 DB를 단순히 많이 쓰이는 개발 학습자료 기준으로 고르는 대신, 잡코리아 채용공고에서 반복적으로 보이는 요구역량을 먼저 정리하고 그 역량을 보완할 한국어 자료로 80개 DB를 다시 구성했다.

## 해석 기준

- 직무군은 기존 프로젝트 범위와 동일하게 4개로 유지했다.
- 채용공고의 `스킬`, `우대조건`, 직무 설명에 등장한 기술명을 우선 근거로 삼았다.
- 단일 공고에만 나온 세부 라이브러리는 바로 DB 1개로 넣지 않고, 같은 계열의 일반 역량으로 묶었다.
- 예: `detectron2`, `mmdetection`은 `Computer Vision / Object Detection`으로 묶고, `Zustand`, `Redux`, `Recoil`은 `상태관리`로 묶었다.
- 학습자료는 한국어 공식문서를 우선하고, 공식 한국어 문서가 부족한 영역은 한국어 강의 검색, 실습플랫폼, 인기 유튜브, 블로그를 보조로 섞었다.

## 잡코리아에서 확인한 반복 요구역량

| 직무군 | 잡코리아 근거 | 확인된 요구역량 | DB 반영 기준 |
|---|---|---|---|
| 데이터 분석가 | 넥슨 데이터 분석가, 콘센트릭스 AI 데이터 분석가, CJ계열 CRM 데이터 분석가, 케어링 데이터 분석가, 웰리시스 Data Analyst, 메이플스토리 데이터 분석가 | Python, SQL, R, Tableau, Excel, AWS/Azure, MySQL, Redash, Spark, Airflow, ML | Python/SQL을 최우선으로 두고, BI/시각화, 클라우드, 대용량 처리, 통계/ML을 보완 축으로 구성 |
| AI/ML 엔지니어 | 로민 ML 엔지니어, 라이다 기반 AI 엔지니어, 동형암호 기업 머신러닝 엔지니어, 빅데이터 AI 개발 공고 | Python, PyTorch, TensorFlow, OpenCV, ONNX, detectron2, mmdetection, LangChain, vLLM, Spark, Hadoop, ML/DL | Python, ML 기초, PyTorch/TensorFlow, CV/객체탐지, LLM, MLOps, 대용량 처리로 구성 |
| 백엔드 개발자 | 아정당 백엔드, 모듈링크 Java/Spring, 로지스밸리 백엔드, 미니게이트 백엔드, 사운드마인드 백엔드 | Java, Spring Boot, JPA/ORM, REST API, Open API, AWS, Docker, CI/CD, Git/GitHub, MariaDB/MySQL, Node.js, Kotlin | Java/Spring/JPA/API를 중심으로 두고, AWS/Docker/CI-CD/Git/DB/테스트를 실무 보완축으로 구성 |
| 프론트엔드 개발자 | 미니게이트 프론트엔드, 제트플레이 프론트엔드, 알엠테크 Frontend, 에피소든 프론트엔드, 토리에듀핀 초급 프론트엔드, 넥스트그라운드 Next.js 인턴 | React, Next.js, TypeScript, JavaScript, Git, Redux, Zustand, Recoil, React Query, Tailwind CSS, Jest, Vite/Webpack, Swagger/OpenAPI | React/Next/TypeScript를 최우선으로 두고, 상태관리, 서버상태, 스타일링, 번들링, 테스트, API 연동을 보완축으로 구성 |

## 재구성 결과

- 총 80개, 직무군별 20개
- 전체 자료 언어는 `한국어`로 통일
- 한국어 공식문서 중심으로 재편하되, 한국어 공식문서가 부족한 실무 기술은 인프런 한국어 검색 결과 또는 한국어 유튜브 채널로 보완
- 데이터 분석가: Python, SQL, Pandas, BI, Spark/Airflow, AWS, 통계/ML
- AI/ML 엔지니어: Python, ML, PyTorch, TensorFlow, CV, ONNX, LLM, MLOps, Spark
- 백엔드 개발자: Java, Spring Boot, JPA, API, AWS, Docker, CI/CD, Git, DB, 테스트
- 프론트엔드 개발자: HTML/CSS/JS, TypeScript, React, Next.js, Git, Tailwind, 상태관리, 테스트, 접근성

## 참고한 잡코리아 공고 URL

- 데이터 분석가: https://www.jobkorea.co.kr/Recruit/GI_Read/48948956
- 데이터 분석가: https://www.jobkorea.co.kr/Recruit/GI_Read/47956533
- 데이터 분석가: https://www.jobkorea.co.kr/Recruit/GI_Read/47613535
- 데이터 분석가/사이언티스트: https://www.jobkorea.co.kr/Recruit/GI_Read/45654948
- ML 엔지니어: https://www.jobkorea.co.kr/Recruit/GI_Read/47343584
- 머신러닝 엔지니어: https://www.jobkorea.co.kr/Recruit/GI_Read/48911668
- AI 엔지니어: https://www.jobkorea.co.kr/Recruit/GI_Read/47140047
- 백엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/47681841
- 백엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/47144246
- 백엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/48889618
- 프론트엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/47322452
- 프론트엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/47013860
- 프론트엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/48070124
- 프론트엔드 개발자: https://www.jobkorea.co.kr/Recruit/GI_Read/46946620

## 한계

- 잡코리아 공고 HTML이 일부 동적 렌더링되어 페이지 본문에서는 `스킬` 값이 비어 보이는 경우가 있었다. 이 경우 검색 결과 스니펫과 열람 가능한 공고 본문을 함께 사용했다.
- 공고는 수시로 마감되거나 수정될 수 있으므로, 발표에서는 “2026-05-20 기준 잡코리아에서 확인한 공고 샘플”이라고 표현한다.
- 이 DB는 시장 전체 통계가 아니라 기말 프로젝트용 샘플 기반 큐레이션이다. 따라서 “전체 시장 평균”보다는 “잡코리아 공고 샘플에서 반복 확인된 요구역량 기반”이라고 설명하는 것이 정확하다.
