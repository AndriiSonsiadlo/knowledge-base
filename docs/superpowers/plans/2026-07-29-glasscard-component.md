# GlassCard Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the homepage's duplicated `.glassCard` CSS-module panel into a reusable `GlassCard` component, and confirm the abandoned `dev/in_progress/home-page-tailwindcss` branch has nothing else worth merging.

**Architecture:** One new presentational component, `src/components/GlassCard/index.tsx`, built with plain Tailwind utility classes (including `dark:` variants — already wired to Docusaurus's `data-theme` attribute via `@custom-variant dark` in `src/css/custom.css`). No CSS module, no new dependency. `src/pages/index.tsx` swaps its two `clsx(styles.glassCard, ...)` divs for `<GlassCard>`, and the now-dead `.glassCard` rules are deleted from `src/pages/index.module.css`.

**Tech Stack:** React 19 (TSX), Tailwind CSS v4, `clsx`/`tailwind-merge` via the existing `cn()` helper (`src/lib/utils.ts`), Docusaurus 3.9.

## Global Constraints

- No test framework is configured in this repo (`CLAUDE.md`: "There is no test suite"). The correctness gate is `npm run build` (`onBrokenLinks: "throw"`) plus `npm run typecheck`. Every task's verification step uses these, not a unit-test runner.
- Formatting/linting is Biome (`npm run format` to auto-fix, `npm run lint` to check) — 2-space indent per `biome.json`.
- Path aliases: use `@components/...` and `@lib/...` (defined in both `src/plugins/webpack-alias.js` and `jsconfig.json`), matching the existing `@components/CategoryGrid` import in `index.tsx`.
- Do not touch `CategoryCard`, `about-me.js`, or merge anything from `origin/dev/in_progress/home-page-tailwindcss` — out of scope per spec (`docs/superpowers/specs/2026-07-29-glasscard-component-design.md`).

---

### Task 1: Create the GlassCard component

**Files:**
- Create: `src/components/GlassCard/index.tsx`

**Interfaces:**
- Produces: `export default function GlassCard({ children, className, hover }: GlassCardProps): JSX.Element`, where `GlassCardProps = { children: React.ReactNode; className?: string; hover?: boolean }`, `hover` defaults to `false`.

- [ ] **Step 1: Write the component**

Base classes are the **light**-mode look (matches how `dark:` is used
elsewhere in this codebase, e.g. `index.tsx:41`, `CategoryGrid/index.tsx:68`
— unprefixed = light, `dark:`-prefixed = dark):

```tsx
import type { ReactNode } from "react";
import { cn } from "@lib/utils";

interface GlassCardProps {
	children: ReactNode;
	className?: string;
	hover?: boolean;
}

export default function GlassCard({
	children,
	className,
	hover = false,
}: GlassCardProps) {
	return (
		<div
			className={cn(
				"relative z-[1] rounded-3xl backdrop-blur-xl",
				"border border-purple-500/20 bg-white/70 shadow-[0_8px_32px_rgba(0,0,0,0.06)]",
				"dark:border-white/10 dark:bg-black/40 dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)]",
				hover &&
					"transition-all duration-300 hover:border-white/30 hover:bg-white/10",
				className,
			)}
		>
			{children}
		</div>
	);
}
```

- [ ] **Step 2: Typecheck**

Run: `npm run typecheck`
Expected: no errors mentioning `GlassCard`.

- [ ] **Step 3: Commit**

```bash
git add src/components/GlassCard/index.tsx
git commit -m "feat: add reusable GlassCard component"
```

---

### Task 2: Wire GlassCard into the homepage and delete dead CSS

**Files:**
- Modify: `src/pages/index.tsx:1-9` (imports), `:33-38` (hero panel), `:76` (categories panel)
- Modify: `src/pages/index.module.css:86-107` (delete `.glassCard` + light override)

**Interfaces:**
- Consumes: `GlassCard` from Task 1 (`export default function GlassCard({ children, className, hover }: GlassCardProps)`), imported as `import GlassCard from "@components/GlassCard";`.

- [ ] **Step 1: Update imports in `index.tsx`**

Add, alongside the existing `CategoryGrid` import:

```tsx
import GlassCard from "@components/GlassCard";
```

- [ ] **Step 2: Replace the hero panel**

Current (`index.tsx:33-38`):

```tsx
						<div
							className={clsx(
								styles.glassCard,
								"p-8 md:p-16 rounded-3xl text-center w-full md:w-3/4 lg:w-2/3",
							)}
						>
```

Replace with:

```tsx
						<GlassCard className="p-8 md:p-16 text-center w-full md:w-3/4 lg:w-2/3">
```

(and change the matching closing `</div>` for this element to `</GlassCard>`).

- [ ] **Step 3: Replace the categories panel**

Current (`index.tsx:76`):

```tsx
						<div className={styles.glassCard}>
```

Replace with:

```tsx
						<GlassCard>
```

(and change its matching closing `</div>` to `</GlassCard>`).

- [ ] **Step 4: Delete the dead CSS**

In `src/pages/index.module.css`, delete the `/* Glass card */` block and the
`html[data-theme="light"] .glassCard` block. Confirm exact current line
numbers first with `grep -n glassCard src/pages/index.module.css` (they may
have shifted since this plan was written) before deleting.

- [ ] **Step 5: Confirm no leftover references**

Run: `grep -rn "glassCard" src/`
Expected: no output (all usages removed).

- [ ] **Step 6: Typecheck and build**

Run: `npm run typecheck && npm run build`
Expected: both succeed with no errors (build also catches any broken links).

- [ ] **Step 7: Commit**

```bash
git add src/pages/index.tsx src/pages/index.module.css
git commit -m "refactor: use GlassCard component on homepage"
```

---

### Task 3: Visual verification and format/lint pass

**Files:** none created/modified (verification only, plus auto-fixes if `npm run format` changes anything).

- [ ] **Step 1: Run the dev server**

Run: `npm run start`

- [ ] **Step 2: Visually compare against current master**

Open the printed local URL. Confirm both the hero panel and the categories
panel render as a glass panel in dark mode. Toggle to light mode via the
navbar theme switch and confirm the panel switches to the light glass look
(soft white, purple-tinted border) — same as it did on master before this
change.

- [ ] **Step 3: Format and lint**

Run: `npm run format && npm run lint`
Expected: no remaining lint errors. If `format` changes files, review the
diff (should be whitespace-only) and include it in the next commit.

- [ ] **Step 4: Final build check**

Run: `npm run build`
Expected: succeeds (production build + link validation).

- [ ] **Step 5: Commit any formatting fixes (only if Step 3 changed files)**

```bash
git add -u
git commit -m "style: format GlassCard changes"
```

---

## Self-Review Notes

- **Spec coverage:** Task 1 covers "Add GlassCard component"; Task 2 covers
  "migrate the two usages" + "remove dead CSS"; Task 3 covers the spec's
  "Testing" section (typecheck/build/visual light+dark check). The spec's
  "Out of scope" section (CategoryCard, about-me.js, DocLayout) has no task
  by design — nothing to implement there.
- **No placeholders:** all steps show literal code/commands.
- **Type consistency:** `GlassCardProps` defined once in Task 1, consumed
  identically in Task 2 (same prop names: `children`, `className`, `hover`).
