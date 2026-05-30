'use strict';
// 사용법: node playwright_extract.cjs <url> [timeout_ms]
// 성공: 본문 텍스트를 stdout에 출력, exit 0
// 실패: 에러 메시지를 stderr에 출력, exit 1
const path = require('path');
const { chromium } = require(
    path.join(__dirname, '..', '..', 'frontend', 'node_modules', 'playwright-core')
);

const url = process.argv[2];
const timeoutMs = parseInt(process.argv[3] || '25000', 10);

if (!url || !url.startsWith('http')) {
    process.stderr.write('Usage: node playwright_extract.cjs <url> [timeout_ms]\n');
    process.exit(1);
}

const noiseSelectors = [
    'nav', 'header', 'footer',
    '.gnb', '.lnb', '.aside', '.sidebar',
    '#header', '#footer', '#nav',
    '[class*="banner"]', '[class*="ad-"]',
];

async function extractText(page) {
    return page.evaluate((selectors) => {
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
        return (document.body.innerText || '').trim();
    }, noiseSelectors);
}

(async () => {
    let browser;
    try {
        browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
            locale: 'ko-KR',
        });
        const page = await context.newPage();

        // 'load' 사용: 일부 페이지는 광고 트래커로 인해 networkidle에 도달하지 못함
        await page.goto(url, {
            waitUntil: 'load',
            timeout: timeoutMs,
        });
        await page.waitForTimeout(2000);

        // 잡코리아: 본문이 동일-도메인 iframe에 로드됨 (GI_Read_Comt_Ifrm)
        // iframe URL을 찾아 별도로 렌더링해 텍스트를 합산
        const iframeSrcs = await page.evaluate(() =>
            [...document.querySelectorAll('iframe')]
                .map(f => f.src)
                .filter(src => src && src.includes('jobkorea.co.kr') && !src.includes('gum.criteo'))
        );

        let mainText = await extractText(page);
        const parts = [mainText];

        for (const iframeSrc of iframeSrcs) {
            try {
                const iframePage = await context.newPage();
                await iframePage.goto(iframeSrc, { waitUntil: 'networkidle', timeout: timeoutMs });
                await iframePage.waitForTimeout(2000);
                const iframeText = await extractText(iframePage);
                if (iframeText) parts.push(iframeText);
                await iframePage.close();
            } catch (_) {}
        }

        const combined = parts.filter(Boolean).join('\n\n').trim();

        if (!combined) {
            process.stderr.write('empty text extracted\n');
            process.exit(1);
        }

        process.stdout.write(combined);
        process.exitCode = 0;
    } catch (err) {
        process.stderr.write(err.message + '\n');
        process.exitCode = 1;
    } finally {
        if (browser) await browser.close();
    }
})();
