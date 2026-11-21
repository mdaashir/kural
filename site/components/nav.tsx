"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useState } from "react";

export function Nav() {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const path = usePathname();
  return <header className="nav"><div className="wrap nav-inner">
    <a className="skip" href="#content">Skip to content</a>
    <Link href="/" className="wordmark" onClick={() => setOpen(false)}>kural<span lang="ta">குரல்</span></Link>
    <button ref={toggle} className="menu" aria-expanded={open} aria-controls="navigation" onClick={() => setOpen(!open)}>{open ? "Close menu" : "Menu"}</button>
    <nav id="navigation" aria-label="Main navigation" className={open ? "nav-links open" : "nav-links"} onKeyDown={e => { if (e.key === "Escape") { setOpen(false); toggle.current?.focus(); } }}>
      <Link href="/docs/" aria-current={path.startsWith("/docs") ? "page" : undefined} onClick={() => setOpen(false)}>Documentation</Link>
      <a href="https://github.com/mdaashir/kural">GitHub ↗</a>
      <Link className="button" href="/downloads/" aria-current={path.startsWith("/downloads") ? "page" : undefined} onClick={() => setOpen(false)}>Download Kural <span aria-hidden="true">↗</span></Link>
    </nav>
  </div></header>;
}
