import type { Metadata } from "next";
import { IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";

import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans"
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono"
});

const productionOrigin = "https://webcompass.ai";
const productionPath = "/WebCompass/";
const productionUrl = `${productionOrigin}${productionPath}`;
const siteUrl = process.env.NODE_ENV === "production" ? productionUrl : "http://localhost:3000/";
const ogImagePath = "/WebCompass/og-image.svg";
const faviconPath = "/WebCompass/favicon.svg";
const paperTitle = "WebCompass: Towards Multimodal Web Coding Evaluation for Code Language Models";

export const metadata: Metadata = {
  title: paperTitle,
  description: "WebCompass: Towards Multimodal Web Coding Evaluation for Code Language Models.",
  metadataBase: new URL(process.env.NODE_ENV === "production" ? productionOrigin : "http://localhost:3000"),
  alternates: {
    canonical: process.env.NODE_ENV === "production" ? productionPath : "/"
  },
  openGraph: {
    title: paperTitle,
    description: "Towards Multimodal Web Coding Evaluation for Code Language Models",
    url: siteUrl,
    siteName: "WebCompass",
    images: [
      {
        url: ogImagePath,
        width: 1200,
        height: 630,
        alt: "WebCompass Project Page"
      }
    ],
    locale: "en_US",
    type: "website"
  },
  twitter: {
    card: "summary_large_image",
    title: paperTitle,
    description: "Towards Multimodal Web Coding Evaluation for Code Language Models",
    images: [ogImagePath]
  },
  icons: {
    icon: faviconPath
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${ibmPlexSans.variable} ${jetbrainsMono.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}

