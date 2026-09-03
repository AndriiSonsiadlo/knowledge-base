#!/usr/bin/env node
// Structural and executable gate for docs/computer-science/algorithms/.
//
//   node tools/check-algo-docs.mjs                                  # the whole section
//   node tools/check-algo-docs.mjs docs/computer-science/algorithms/complexity
//   node tools/check-algo-docs.mjs docs/.../complexity/big-o-notation.md
//
// Structural checks are cheap and always run. On top of them, every `python`
// fence on a page is concatenated in document order and executed, and every
// `cpp` fence is concatenated and syntax-checked, because a documentation page
// that ships code nobody ran is a page that ships bugs.
//
// A fence whose first line is `# doc:no-run` (python) or `// doc:no-run` (cpp)
// is skipped and counted — for illustrative fragments and code needing input.
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";

const DEFAULT_ROOT = "docs/computer-science/algorithms";
const MIN_LINES = 150;
const MAX_LINES = 340;
const FRONTMATTER_KEYS = ["id", "title", "sidebar_label", "sidebar_position", "tags"];

const findings = [];
const note = (file, msg) => findings.push(`${file}: ${msg}`);
let skippedFences = 0;

const HAS_GXX = spawnSync("g++", ["--version"], { stdio: "ignore" }).status === 0;

function collect(target) {
	const st = statSync(target);
	if (st.isFile()) return [target];
	return readdirSync(target, { recursive: true, withFileTypes: true })
		.filter((d) => d.isFile() && d.name.endsWith(".md"))
		.map((d) => join(d.parentPath ?? d.path, d.name))
		.sort();
}

function frontmatter(text) {
	const m = text.match(/^---\n([\s\S]*?)\n---\n/);
	if (!m) return null;
	const out = {};
	for (const line of m[1].split("\n")) {
		const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
		if (kv) out[kv[1]] = kv[2].trim();
	}
	return out;
}

function fences(text, lang) {
	const re = new RegExp("^```" + lang + "[^\\n]*\\n([\\s\\S]*?)^```", "gm");
	const out = [];
	let m;
	while ((m = re.exec(text)) !== null) out.push(m[1]);
	return out;
}

function runnable(blocks, marker) {
	return blocks.filter((b) => {
		const skip = b.split("\n")[0].trim() === marker;
		if (skip) skippedFences++;
		return !skip;
	});
}

function tempFile(name, contents) {
	const path = join(mkdtempSync(join(tmpdir(), "algo-docs-")), name);
	writeFileSync(path, contents);
	return path;
}

function tail(s, n = 6) {
	return (s ?? "").trim().split("\n").slice(-n).join("\n        ");
}

// ------------------------------------------------------------------ per page
function checkPage(file, positions) {
	const text = readFileSync(file, "utf8");
	const name = basename(file);
	const isCheatSheet = name === "cheat-sheet.md";

	const fm = frontmatter(text);
	if (!fm) {
		note(file, "no frontmatter block");
	} else {
		for (const k of FRONTMATTER_KEYS) {
			if (!(k in fm)) note(file, `frontmatter missing \`${k}\``);
		}
		const pos = fm.sidebar_position;
		if (pos !== undefined) {
			const folder = dirname(file);
			const seen = positions.get(folder) ?? new Map();
			if (seen.has(pos)) note(file, `duplicate sidebar_position ${pos} (also ${seen.get(pos)})`);
			else seen.set(pos, basename(file));
			positions.set(folder, seen);
		}
	}

	const recallAt = text.indexOf("<Recall");
	if (recallAt === -1) note(file, "no <Recall> card");
	else {
		const recallHeadingAt = text.search(/^## Recall\s*$/m);
		const referencesAt = text.search(/^## References\s*$/m);
		if (recallHeadingAt === -1) note(file, "<Recall> card is not under its own `## Recall` heading");
		else if (recallHeadingAt > recallAt) note(file, "<Recall> card appears before its `## Recall` heading");
		else if (referencesAt !== -1 && recallHeadingAt > referencesAt)
			note(file, "`## Recall` section appears after `## References`, must come directly before it");
	}

	if (!/^## References\s*$/m.test(text)) note(file, "no `## References` section");
	if (!/^## Related Pages\s*$/m.test(text)) note(file, "no `## Related Pages` section");

	const hasVisual = /<Figure/.test(text) || /^```mermaid/m.test(text) || /^```text/m.test(text);
	if (!hasVisual) note(file, "no visual anchor (<Figure, mermaid fence, or text trace block)");

	const lines = text.split("\n").length;
	if (!isCheatSheet && lines < MIN_LINES) note(file, `${lines} lines — under the ${MIN_LINES} floor`);
	if (!isCheatSheet && lines > MAX_LINES) note(file, `${lines} lines — over the ${MAX_LINES} ceiling`);

	// --- python
	const py = runnable(fences(text, "python"), "# doc:no-run");
	if (py.length) {
		const src = py.join("\n\n");
		if (!/^\s*assert\b/m.test(src)) note(file, "runnable python fences but not one assert");
		const r = spawnSync("python3", [tempFile("page.py", src)], { encoding: "utf8", timeout: 60000 });
		if (r.status !== 0) note(file, `python fences failed:\n        ${tail(r.stderr || r.stdout)}`);
	}

	// --- c++
	const cpp = runnable(fences(text, "cpp"), "// doc:no-run");
	if (cpp.length && HAS_GXX) {
		const src = cpp.join("\n\n");
		const r = spawnSync("g++", ["-fsyntax-only", "-std=c++20", tempFile("page.cpp", src)], {
			encoding: "utf8",
			timeout: 120000,
		});
		if (r.status !== 0) note(file, `c++ fences failed to compile:\n        ${tail(r.stderr || r.stdout)}`);
	}
}

// ---------------------------------------------------------------------- main
const targets = process.argv.slice(2).length ? process.argv.slice(2) : [DEFAULT_ROOT];
const files = targets.flatMap(collect);
const positions = new Map();
for (const f of files) checkPage(f, positions);

if (!HAS_GXX) console.warn("warning: g++ not found — c++ fences were not syntax-checked");
console.log(`${files.length} pages checked, ${skippedFences} fences skipped via doc:no-run`);

if (findings.length) {
	console.error(`\n${findings.length} finding(s):`);
	for (const f of findings) console.error(`  ${f}`);
	process.exit(1);
}
console.log("clean");
