#!/usr/bin/env node
// Authoring-convention gate for docs/linux/.
//
//   node tools/check-linux-docs.mjs             # structure only; stubs exempt
//   node tools/check-linux-docs.mjs --written   # every page must be finished
//
// The knowledge-graph plugin already fails the build on a bad prerequisite id
// or a cycle. This covers the conventions the plugin cannot see: category
// descriptions (Rule 2), required front matter, and — for finished pages —
// the closing facts card and the references section.
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const ROOT = "docs/linux";
const REQUIRED_KEYS = ["title", "sidebar_label", "sidebar_position", "tags", "prerequisites"];
const STUB_MARKER = ":::info[Not yet written]";
const requireWritten = process.argv.includes("--written");

// Navigational pages: they carry no topic of their own, so the closing facts
// card and the references section do not apply to them. Front-matter and
// category checks still do.
const NAVIGATIONAL = new Set([
  "docs/linux/readme.md",
  "docs/linux/00-overview/roadmap.md",
  "docs/linux/00-overview/glossary.md",
  "docs/linux/00-overview/misconceptions-index.md",
  "docs/linux/00-overview/how-to-use-this-section.md",
]);

const findings = [];
const note = (file, message) => findings.push(`${file}: ${message}`);

function markdownFiles(dir) {
  return readdirSync(dir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && /\.mdx?$/.test(entry.name))
    .map((entry) => join(entry.parentPath ?? entry.path, entry.name))
    .sort();
}

function frontmatter(text) {
  const match = text.match(/^---\n([\s\S]*?)\n---/);
  return match ? match[1] : null;
}

// Rule 2: every folder's category file carries a real description.
for (const entry of readdirSync(ROOT, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const path = join(ROOT, entry.name, "_category_.json");
  if (!existsSync(path)) {
    note(path, "missing — every folder needs a _category_.json");
    continue;
  }
  const category = JSON.parse(readFileSync(path, "utf8"));
  const description = category.link?.description;
  if (!description || description.trim().length < 20) {
    note(path, 'link.description is missing or too short — it is a required field, one real sentence');
  }
  if (typeof category.position !== "number") {
    note(path, "position must be a number");
  }
}

let stubs = 0;
let written = 0;

for (const file of markdownFiles(ROOT)) {
  const text = readFileSync(file, "utf8");
  const front = frontmatter(text);
  if (!front) {
    note(file, "no front matter");
    continue;
  }

  for (const key of REQUIRED_KEYS) {
    if (!new RegExp(`^${key}:`, "m").test(front)) {
      note(file, `front matter is missing "${key}"`);
    }
  }

  if (text.includes(STUB_MARKER)) {
    stubs += 1;
    if (requireWritten) {
      note(file, "still a stub, but --written was requested");
    }
    continue;
  }

  written += 1;
  if (NAVIGATIONAL.has(file.split("\\").join("/"))) continue;
  if (!text.includes("<KernelFacts")) {
    note(file, "a finished page must end with a <KernelFacts /> card");
  }
  if (!/^## References$/m.test(text)) {
    note(file, "a finished page must have a ## References section");
  }
}

if (findings.length > 0) {
  console.error(`check-linux-docs: ${findings.length} finding(s)\n`);
  for (const finding of findings) console.error(`  ${finding}`);
  process.exit(1);
}

console.log(`check-linux-docs: OK — ${written} written page(s), ${stubs} stub(s)`);
