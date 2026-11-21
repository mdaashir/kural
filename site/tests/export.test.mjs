import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

const root = join(import.meta.dirname, "..", "out");
const pages = ["", "downloads", "docs", "docs/quickstart", "docs/commands", "docs/api", "docs/config", "docs/troubleshooting"];
const html = pages.map(path => {
  const file = join(root, path, "index.html");
  assert.ok(existsSync(file), `missing export: ${file}`);
  return readFileSync(file, "utf8");
});

test("all static pages have a title, canonical and GitHub Pages asset paths", () => {
  for (const [index, page] of html.entries()) {
    assert.match(page, /<title>[^<]+<\/title>/);
    assert.match(page, /rel="canonical"[^>]+https:\/\/mdaashir\.github\.io\/kural\//);
    assert.match(page, /\/_next\/static/); // Next emits basePath-prefixed assets, checked below
    assert.match(page, /\/kural\/_next\/static/);
    assert.doesNotMatch(page, /(?:src|href)="\/_next\//);
    assert.match(page, /<main\b/);
    assert.match(page, /Skip to content/);
    assert.ok(index === 0 || page.includes('href="/kural/docs/'), `missing docs navigation: ${pages[index]}`);
  }
});

test("local links stay within the base path and target exported pages or assets", () => {
  const hrefs = [...html.join("\n").matchAll(/\bhref="([^"]+)"/g)].map(match => match[1]);
  for (const href of hrefs) {
    if (!href.startsWith("/")) continue;
    assert.ok(href.startsWith("/kural/"), `unprefixed href: ${href}`);
    const path = href.slice("/kural/".length).split(/[?#]/)[0];
    const target = join(root, path, path.endsWith("/") || !path.includes(".") ? "index.html" : "");
    assert.ok(existsSync(target), `broken local link: ${href} -> ${target}`);
  }
});

test("download and safety statements reflect the product", () => {
  assert.match(html[1], /releases\/download\/v0\.1\.3\/kural-windows-x64-setup\.exe/);
  assert.match(html[1], /releases\/download\/v0\.1\.3\/kural-windows-x64\.zip/);
  assert.match(html[1], /pypi\.org\/project\/cmd-kural\/0\.1\.3/);
  assert.match(html[1], /SHA256SUMS/);
  assert.match(html[1], /releases\/download\/v0\.1\.3\/cmd_kural-0\.1\.3-py3-none-any\.whl/);
  assert.match(html[0], /Preset text only\. No microphone access or live transcription/);
  assert.match(html[0], /Models download on first use/);
  assert.match(html[6], /Incognito disables history, learning, retained audio and Paste Last memory/);
  assert.match(html[5], /127\.0\.0\.1:7777/);
  assert.match(html[0], /GitHub may collect technical request logs/);
  assert.doesNotMatch(html.join("\n"), /(?:Google Analytics|gtag\(|cloud inference service required)/i);
});

test("metadata route and local artwork are exported", () => {
  for (const asset of ["robots.txt", "sitemap.xml", "icon.svg", "og.svg"]) assert.ok(existsSync(join(root, asset)), asset);
  const sitemap = readFileSync(join(root, "sitemap.xml"), "utf8");
  for (const page of pages) assert.ok(sitemap.includes(`https://mdaashir.github.io/kural/${page}${page ? "/" : ""}`), page);
  assert.match(readFileSync(join(root, "robots.txt"), "utf8"), /https:\/\/mdaashir\.github\.io\/kural\/sitemap\.xml/);
});
