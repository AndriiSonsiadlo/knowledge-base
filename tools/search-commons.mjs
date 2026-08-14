#!/usr/bin/env node
import { readFile } from "node:fs/promises";
const UA = "knowledge-base-docs/1.0";
const queries = JSON.parse(await readFile(process.argv[2], "utf8"));
for (const q of queries) {
  const u = `https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srnamespace=6&srlimit=8&srsearch=${encodeURIComponent(q)}`;
  const j = await fetch(u, { headers: { "User-Agent": UA } }).then((r) => r.json());
  console.log(`\n### ${q}`);
  for (const s of j.query.search) console.log("  " + s.title);
}
