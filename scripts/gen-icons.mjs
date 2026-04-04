// Regenerates src/components/lucide-subset.json — a tiny, curated offline set of
// lucide icons bundled for the MDX <Icon /> component (see src/theme/MDXComponents.js).
// Keep the list small: only icons actually used in docs, so the per-page bundle stays light.
//
//   node scripts/gen-icons.mjs
//
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const full = require("@iconify-json/lucide/icons.json");

const WANT = [
	// reading-path personas
	"rocket", "arrow-left-right", "cpu",
	// one per C++ section (overview landing map)
	"book-open", "wrench", "braces", "shapes", "square-function", "memory-stick",
	"pointer", "boxes", "blocks", "library", "shield-check", "waypoints",
	"binary", "drafting-compass", "bug", "layers",
	// CMake sections
	"target", "package", "folder-tree", "flask-conical", "settings",
];

const out = { prefix: "lucide", icons: {}, width: full.width ?? 24, height: full.height ?? 24 };
const missing = [];
for (const name of WANT) {
	if (full.icons[name]) out.icons[name] = full.icons[name];
	else missing.push(name);
}
if (missing.length) {
	console.error("Unknown lucide icons:", missing.join(", "));
	process.exit(1);
}

writeFileSync("src/components/lucide-subset.json", JSON.stringify(out));
console.log(`wrote ${Object.keys(out.icons).length} icons to src/components/lucide-subset.json`);
