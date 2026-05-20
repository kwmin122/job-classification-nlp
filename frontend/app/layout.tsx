import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JD Skill Gap RAG Dashboard",
  description: "D-part local dashboard for curated learning-resource recommendations"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

