from __future__ import annotations

from collections import Counter

from app.services.resource_loader import load_resources


REQUIRED_JOB_GROUPS = {"데이터 분석가", "AI/ML 엔지니어", "백엔드 개발자", "프론트엔드 개발자"}


def main() -> None:
    resources = load_resources()
    urls = [resource.url for resource in resources]
    job_counts = Counter(resource.job_group for resource in resources)
    duplicate_urls = [url for url, count in Counter(urls).items() if count > 1]
    invalid_reliability = [
        resource.id for resource in resources if resource.reliability < 1 or resource.reliability > 5
    ]

    print(f"resource_count={len(resources)}")
    print(f"job_group_counts={dict(sorted(job_counts.items()))}")
    print(f"duplicate_url_count={len(duplicate_urls)}")
    print(f"invalid_reliability_count={len(invalid_reliability)}")

    if len(resources) < 80:
        raise SystemExit("FAIL: learning resource DB must contain at least 80 rows")
    missing_groups = REQUIRED_JOB_GROUPS - set(job_counts)
    if missing_groups:
        raise SystemExit(f"FAIL: missing job groups: {sorted(missing_groups)}")
    if duplicate_urls:
        raise SystemExit(f"FAIL: duplicate URLs found: {duplicate_urls[:5]}")
    if invalid_reliability:
        raise SystemExit(f"FAIL: invalid reliability rows: {invalid_reliability[:5]}")

    print("audit_status=PASS")


if __name__ == "__main__":
    main()
