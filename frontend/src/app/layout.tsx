import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sentinel AI — Multi-Agent Scam Investigation Network",
  description:
    "Sentinel AI investigates suspicious messages using a coordinated network of specialist reasoning agents, built on Microsoft Foundry.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
