import type { Metadata } from "next";
export const origin = "https://mdaashir.github.io";
export const base = `${origin}/kural`;
export const repo = "https://github.com/mdaashir/kural";
export const release = `${repo}/releases/download/v0.1.3`;
export const routes = ["/", "/downloads/", "/docs/", "/docs/quickstart/", "/docs/commands/", "/docs/api/", "/docs/config/", "/docs/troubleshooting/"];
export function metadata(title: string, description: string, path: string): Metadata {
  return { title, description, alternates: { canonical: `${base}${path}` }, openGraph: { title: `${title} | Kural`, description, url: `${base}${path}`, type: "website", images: [{ url: `${base}/og.svg`, width: 1200, height: 630, alt: "Kural — local voice typing for Windows" }] } };
}
export const docs = [
  ["quickstart", "Quickstart", "Install Kural and dictate your first sentence."],
  ["commands", "Commands", "Use hotkeys, file transcription and diagnostics."],
  ["api", "Local API", "Transcribe audio files through a loopback-bound API."],
  ["config", "Configuration", "Choose your language, model and text delivery."],
  ["troubleshooting", "Troubleshooting", "Check your microphone, GPU and text insertion."],
] as const;
