import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Nav } from "../components/nav";
import { base, repo } from "../lib/site";
import "./globals.css";
export const metadata: Metadata = {
  metadataBase: new URL(`${base}/`),
  title: { default: "Kural — local voice typing for Windows", template: "%s | Kural" },
  description: "Local Windows voice typing in English and Tamil, with Tanglish command aliases. Powered by Whisper on your computer.",
  twitter: { card: "summary_large_image", images: [`${base}/og.svg`] },
  icons: { icon: "/kural/icon.svg" },
  other: { "page-type": "software", "site-kind": "software" },
};
export const viewport: Viewport = { themeColor: "#f5f3eb" };
export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="en" data-type="software"><body><Nav /><main id="content" tabIndex={-1}>{children}</main><footer><div className="wrap"><div className="footer-top"><Link className="wordmark" href="/">kural<span lang="ta">குரல்</span></Link><p>Your voice. Your computer.</p></div><div className="footer-bottom"><span>Open source · MIT licensed</span><nav aria-label="Footer"><Link href="/docs/quickstart/">Quickstart</Link><Link href="/docs/api/">Local API</Link><a href={`${repo}/blob/main/LICENSE`}>License</a><a href={`${repo}/issues`}>Report an issue ↗</a></nav></div><p className="small">This site has no analytics. Hosted on GitHub Pages; GitHub may collect technical request logs.</p></div></footer></body></html>;
}
