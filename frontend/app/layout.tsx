import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "역량 핏 분석",
  description: "채용공고 기반 역량 격차와 학습 로드맵 추천 대시보드"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <head>
        {/* Pretendard — Korean system font */}
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"/>
        {/* Inter + Space Grotesk via Google Fonts */}
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet"/>
      </head>
      <body>{children}</body>
    </html>
  );
}
