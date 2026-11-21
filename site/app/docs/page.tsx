import Link from "next/link";
import { DocsShell } from "../../components/docs-shell";
import { docs, metadata as meta } from "../../lib/site";
export const metadata = meta("Documentation", "Install, configure and troubleshoot Kural local voice typing and its loopback API.", "/docs/");
export default function Docs() { return <DocsShell current="index"><p className="eyebrow">Documentation</p><h1>Work with Kural</h1><p className="lead">Install the desktop app, set up local Whisper transcription, or use the optional loopback API. Start with a microphone and a plain text editor.</p><div className="cards">{docs.map(([slug,title,description]) => <Link key={slug} href={`/docs/${slug}/`}><h2>{title} ↗</h2><p>{description}</p></Link>)}</div><p>Kural is open source. <a href="https://github.com/mdaashir/kural/issues">Report an issue on GitHub</a>.</p></DocsShell>; }
