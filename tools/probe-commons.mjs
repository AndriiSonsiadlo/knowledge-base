#!/usr/bin/env node
import { readFile } from "node:fs/promises";
const UA = "knowledge-base-docs/1.0";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function getJSON(u) {
  for (let a = 0; a < 6; a++) {
    const r = await fetch(u, { headers: { "User-Agent": UA } });
    const t = await r.text();
    try { return JSON.parse(t); } catch { await sleep(3000 * (a + 1)); }
  }
  throw new Error("API kept failing: " + u);
}
const titles = (await readFile(process.argv[2], "utf8")).split("\n").map(s=>s.trim()).filter(Boolean);
for (let i = 0; i < titles.length; i += 40) {
  const chunk = titles.slice(i, i + 40);
  const u = `https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata&titles=${encodeURIComponent(chunk.join("|"))}`;
  const j = await getJSON(u);
  for (const p of Object.values(j.query.pages)) {
    if (p.missing !== undefined) { console.log(`MISS  ${p.title}`); continue; }
    const ii = p.imageinfo?.[0];
    const lic = (ii?.extmetadata?.LicenseShortName?.value ?? "?").replace(/<[^>]*>/g,"");
    console.log(`OK    ${String(ii?.width)+"x"+String(ii?.height)}  ${lic.padEnd(16)}  ${p.title}`);
  }
  await sleep(2000);
}
