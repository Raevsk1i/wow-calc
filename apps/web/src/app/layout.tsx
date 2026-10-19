import type { Metadata } from "next";
import { Cinzel, Source_Sans_3 } from "next/font/google";

import "./globals.css";
import { Providers } from "@/components/Providers";

const display = Cinzel({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "700"],
});

const body = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "600", "700"],
});

export const metadata: Metadata = {
  title: "WoW DPS Lab — Midnight 12.1.5",
  description: "DPS-калькулятор World of Warcraft: Midnight 12.1.5 (Fast Estimate + SimulationCraft Accurate)",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru" className={`${display.variable} ${body.variable}`}>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
