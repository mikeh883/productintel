import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProductIntel Knowledge",
  description: "RAG chat over the knowledge base, powered by Google ADK.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
