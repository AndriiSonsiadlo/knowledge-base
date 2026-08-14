#!/usr/bin/env node
// Fetch figures from Wikimedia Commons together with their licence metadata.
//
//   node tools/fetch-commons.mjs <manifest.json> [rows-out.md]
//
// Manifest entries: { "file": "File:Foo.svg", "dest": "cs/section/name.png", "width": 900 }
// SVG sources are fetched as Commons' own PNG rendering (stable across browsers);
// animated GIFs are fetched as originals, since a thumbnail is a single frozen frame.
//
// Commons rate-limits aggressively and answers with an HTML error page rather than an
// HTTP error, so every response is validated by magic bytes before it is written.
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const UA = "knowledge-base-docs/1.0 (https://github.com/AndriiSonsiadlo/knowledge-base)";
const API = "https://commons.wikimedia.org/w/api.php";
const THROTTLE_MS = 1500;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const strip = (html) =>
	(html ?? "")
		.replace(/<[^>]*>/g, " ")
		.replace(/&amp;/g, "&")
		.replace(/&quot;/g, '"')
		.replace(/&#0?39;/g, "'")
		.replace(/&nbsp;/g, " ")
		.replace(/\s+/g, " ")
		.trim();

const MAGIC = {
	png: (b) => b.length > 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47,
	gif: (b) => b.length > 6 && b.subarray(0, 3).toString("latin1") === "GIF",
	jpg: (b) => b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff,
};

const looksLikeImage = (buf, dest) => {
	const ext = dest.split(".").pop().toLowerCase();
	const check = MAGIC[ext === "jpeg" ? "jpg" : ext];
	return check ? check(buf) : false;
};

async function getJSON(url) {
	for (let attempt = 0; attempt < 6; attempt++) {
		const res = await fetch(url, { headers: { "User-Agent": UA } });
		const text = await res.text();
		try {
			return JSON.parse(text);
		} catch {
			await sleep(4000 * (attempt + 1));
		}
	}
	throw new Error(`API never returned JSON: ${url}`);
}

async function getImage(url, dest) {
	for (let attempt = 0; attempt < 6; attempt++) {
		const res = await fetch(url, { headers: { "User-Agent": UA } });
		const buf = Buffer.from(await res.arrayBuffer());
		if (res.ok && looksLikeImage(buf, dest)) return buf;
		await sleep(4000 * (attempt + 1));
	}
	return null;
}

const manifest = JSON.parse(await readFile(process.argv[2], "utf8"));
const rows = [];
const failures = [];

for (const entry of manifest) {
	const url = `${API}?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=${entry.width ?? 900}&titles=${encodeURIComponent(entry.file)}`;
	const meta = await getJSON(url);
	const page = Object.values(meta.query.pages)[0];
	if (!page?.imageinfo) {
		failures.push(`${entry.file}: not found on Commons`);
		continue;
	}
	const info = page.imageinfo[0];
	const em = info.extmetadata ?? {};

	const animated = entry.file.toLowerCase().endsWith(".gif");
	const src = ((animated ? info.url : (info.thumburl ?? info.url)) ?? "").split("?")[0];

	await sleep(THROTTLE_MS);
	const bin = await getImage(src, entry.dest);
	if (!bin) {
		failures.push(`${entry.file}: download never yielded a valid image`);
		continue;
	}

	const out = join("static/img", entry.dest);
	await mkdir(dirname(out), { recursive: true });
	await writeFile(out, bin);

	rows.push({
		dest: entry.dest,
		desc: info.descriptionurl,
		author: strip(em.Artist?.value) || "unknown",
		license: strip(em.LicenseShortName?.value) || "unknown",
	});
	console.log(
		`OK  ${(bin.length / 1024).toFixed(0).padStart(5)} KB  ${rows.at(-1).license.padEnd(14)}  ${entry.dest}`,
	);
	await sleep(THROTTLE_MS);
}

if (process.argv[3]) {
	await writeFile(
		process.argv[3],
		`${rows
			.map((r) => `| \`${r.dest.replace(/^cs\//, "")}\` | ${r.desc} | ${r.author} | ${r.license} |`)
			.join("\n")}\n`,
	);
}

if (failures.length) {
	console.error(`\n${failures.length} FAILED:`);
	for (const f of failures) console.error(`  ${f}`);
	process.exit(1);
}
