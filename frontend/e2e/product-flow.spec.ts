import { expect, test } from "@playwright/test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const jobPostingText =
  "백엔드 개발자 채용. 주요 업무는 Spring Boot 기반 REST API 개발, MySQL 데이터 모델링, Docker 컨테이너 기반 배포, AWS 클라우드 운영, CI/CD 파이프라인 구축입니다. Kubernetes와 Kafka 경험을 우대합니다.";

const candidateText =
  "저는 Java와 Spring Boot를 사용해 주문 관리 REST API를 개발했습니다. MySQL 테이블 설계와 SQL 튜닝 경험이 있고, GitHub README에 API 명세를 정리했습니다. Docker, AWS, CI/CD 운영 경험은 아직 부족합니다.";

test("사용자가 텍스트를 입력하면 분석 결과, 추천 자료, 주차별 로드맵이 렌더링된다", async ({ page }) => {
  await page.goto("/");

  const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
  await expect(jobPanel).toHaveCount(1);
  await jobPanel.locator("textarea").fill(jobPostingText);

  const candidatePanel = page.locator('section[aria-label="내 지원 자료"]');
  await expect(candidatePanel).toHaveCount(1);
  await candidatePanel.locator("textarea").fill(candidateText);

  await page.getByRole("button", { name: "분석 시작" }).click();

  await expect(page.getByRole("button", { name: "분석 중입니다" })).toBeVisible();
  const scoreBoard = page.locator(".score-board");
  await expect(scoreBoard).toBeVisible({ timeout: 180_000 });
  await expect(scoreBoard.getByText("예측 직무", { exact: true })).toBeVisible();
  await expect(scoreBoard.getByText("적합도", { exact: true })).toBeVisible();
  await expect(scoreBoard.getByText("부족 역량", { exact: true })).toBeVisible();
  await expect(page.getByText("Weekly Roadmap")).toBeVisible();
  await expect(page.getByText("Curated RAG Resources")).toBeVisible();
  await expect(page.locator(".resource-column a").first()).toBeVisible();
});

test("사용자가 JD 텍스트 + 지원자 TXT 파일 업로드로 분석할 수 있다", async ({ page }) => {
  const tempDir = mkdtempSync(join(tmpdir(), "jd-rag-e2e-"));
  const candidateFile = join(tempDir, "resume.txt");
  writeFileSync(candidateFile, candidateText, "utf-8");

  await page.goto("/");

  const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
  await jobPanel.getByRole("button", { name: "텍스트" }).click();
  await jobPanel.locator("textarea").fill(jobPostingText);
  await expect(jobPanel.locator("textarea")).toContainText("Docker 컨테이너 기반 배포");

  const candidatePanel = page.locator('section[aria-label="내 지원 자료"]');
  await candidatePanel.locator('input[type="file"]').setInputFiles(candidateFile);
  await expect(candidatePanel.locator("textarea")).toContainText("Spring Boot를 사용해 주문 관리 REST API");

  await page.getByRole("button", { name: "분석 시작" }).click();

  await expect(page.locator(".score-board")).toBeVisible({ timeout: 180_000 });
  await expect(page.getByText("역량별 추천 자료")).toBeVisible();
  await expect(page.getByText("4주 학습 계획")).toBeVisible();
});

test("JD URL 탭이 기본으로 활성화되어 있고 텍스트 전환 후 분석이 완료된다", async ({ page }) => {
  await page.goto("/");

  const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
  // URL tab should be selected by default
  const urlBtn = jobPanel.getByRole("button", { name: "URL", exact: true });
  await expect(urlBtn).toHaveClass(/selected/);

  // Switch to text and fill
  await jobPanel.getByRole("button", { name: "텍스트" }).click();
  await jobPanel.locator("textarea").fill(jobPostingText);

  const candidatePanel = page.locator('section[aria-label="내 지원 자료"]');
  await candidatePanel.locator("textarea").fill(candidateText);

  await page.getByRole("button", { name: "분석 시작" }).click();

  await expect(page.locator(".score-board")).toBeVisible({ timeout: 180_000 });
  await expect(page.getByText("Curated RAG Resources")).toBeVisible();
});
