import Link from "next/link";
import { docs } from "../lib/site";

export function DocsShell({ children, current }: { children: React.ReactNode; current: string }) {
  return <div className="content-page"><div className="wrap doc-layout"><nav className="doc-nav" aria-label="Documentation sections"><Link href="/docs/" aria-current={current === "index" ? "page" : undefined}>Overview</Link>{docs.map(([slug, title]) => <Link key={slug} href={`/docs/${slug}/`} aria-current={current === slug ? "page" : undefined}>{title}</Link>)}</nav><article>{children}</article></div></div>;
}
