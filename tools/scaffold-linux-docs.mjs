#!/usr/bin/env node
// Creates the docs/linux/ page tree from tools/linux-docs-manifest.json.
//
//   node tools/scaffold-linux-docs.mjs           # create anything missing
//   node tools/scaffold-linux-docs.mjs --force   # also overwrite existing pages
//
// Implements Rule 1 of the section spec: every page in a phase exists as a
// one-sentence stub before any page is written properly, so that links and
// prerequisite ids resolve from the phase's first commit.
//
// Existing .md files are never touched without --force. Re-running this after
// pages have been written is safe and is how later phases extend the tree.
import { mkdirSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const MANIFEST = "tools/linux-docs-manifest.json";
const force = process.argv.includes("--force");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));

let created = 0;
let skipped = 0;
let categories = 0;

function yamlList(key, values) {
  if (!values || values.length === 0) return `${key}: []`;
  return [`${key}:`, ...values.map((v) => `  - ${v}`)].join("\n");
}

function stub(page, folder) {
  const front = [
    "---",
    `id: ${page.id}`,
    `title: "${page.title}"`,
    `sidebar_label: "${page.sidebar_label}"`,
    `sidebar_position: ${page.sidebar_position}`,
    `tags: [${page.tags.join(", ")}]`,
    yamlList("prerequisites", page.prerequisites),
    ...(page.related?.length ? [yamlList("related", page.related)] : []),
    "draft: false",
    "---",
    "",
    `# ${page.title}`,
    "",
    page.summary,
    "",
    ":::info[Not yet written]",
    `This page is a stub. See [the roadmap](${folder.roadmapLink}) for what lands when.`,
    ":::",
    "",
  ];
  return front.join("\n");
}

function writeIfAbsent(path, contents) {
  mkdirSync(dirname(path), { recursive: true });
  if (existsSync(path) && !force) {
    skipped += 1;
    return;
  }
  writeFileSync(path, contents);
  created += 1;
}

for (const folder of manifest.folders) {
  const dir = join(manifest.root, folder.dir);
  mkdirSync(dir, { recursive: true });

  writeFileSync(
    join(dir, "_category_.json"),
    `${JSON.stringify(
      {
        label: folder.label,
        position: folder.position,
        link: { type: "generated-index", description: folder.description },
      },
      null,
      2,
    )}\n`,
  );
  categories += 1;

  for (const page of folder.pages) {
    writeIfAbsent(join(dir, page.file), stub(page, folder));
  }
}

// Prerequisite pages that live outside docs/linux/. Same stub shape, minus the
// prerequisites key, which only in-scope pages are required to carry.
for (const page of manifest.external ?? []) {
  const body = [
    "---",
    `id: ${page.id}`,
    `title: "${page.title}"`,
    `sidebar_label: "${page.sidebar_label}"`,
    `sidebar_position: ${page.sidebar_position}`,
    `tags: [${page.tags.join(", ")}]`,
    "draft: false",
    "---",
    "",
    `# ${page.title}`,
    "",
    page.summary,
    "",
    ":::info[Not yet written]",
    "This page is a stub, created as a prerequisite for the Linux & Kernel section.",
    ":::",
    "",
  ].join("\n");
  writeIfAbsent(page.path, body);
}

console.log(
  `scaffold: ${created} file(s) created, ${skipped} left alone, ${categories} category file(s) written`,
);
