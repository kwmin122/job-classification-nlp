import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JD Fit Roadmap",
  description: "채용공고 기반 역량 격차와 학습 로드맵 추천 대시보드"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
