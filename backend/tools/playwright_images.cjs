'use strict';
// 사용법: node playwright_images.cjs <url> [timeout_ms]
// 페이지의 '큰 콘텐츠 이미지'(JD 포스터 추정) URL을 한 줄씩 stdout에 출력.
const path = require('path');
const { chromium } = require(
    path.join(__dirname, '..', '..', 'frontend', 'node_modules', 'playwright-core')
);
(async () => {
  const url = process.argv[2];
  const timeout = parseInt(process.argv[3] || '25000', 10);
  if (!url || !url.startsWith('http')) { process.exit(1); }
  let b;
  try {
    b = await chromium.launch();
    const p = await (await b.newContext({ userAgent: 'Mozilla/5.0 (compatible; JD-Fit-Roadmap/0.1)', locale: 'ko-KR' })).newPage();
    await p.goto(url, { waitUntil: 'networkidle', timeout });
    await p.waitForTimeout(2000);
    const urls = await p.evaluate(() =>
      [...document.querySelectorAll('img')]
        .filter(i => i.naturalHeight > 500 && i.naturalWidth > 200)
        .map(i => i.src)
        .filter(s => s && s.startsWith('http'))
    );
    process.stdout.write([...new Set(urls)].join('\n'));
  } catch (e) {
    // graceful: 빈 출력
  } finally { if (b) await b.close(); }
})();
