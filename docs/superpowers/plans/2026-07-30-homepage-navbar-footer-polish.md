# Home page / navbar / footer polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the Categories title/navbar-icon/footer/card-hover inconsistencies called out in the spec, and add homepage stat counters, scroll-reveal animation, docs-page reading polish, and a back-to-top + cursor-glow touch — all using plain CSS + small React hooks, no new dependencies.

**Architecture:** Pure CSS edits for the four "fix" items (title gradient, icon parity, card glow, footer gradient). Two new small, reusable primitives (`ScrollReveal`, `useCountUp`) consumed by a new `StatsSection` component and wrapped around existing homepage sections. Docs polish is CSS-only plus edits to the already-swizzled `src/theme/DocItem/Layout`. Back-to-top and cursor-glow are two new standalone components, the former mounted via a new `src/theme/Root` swizzle (none exists yet).

**Tech Stack:** Docusaurus 3.9 (React 19), Tailwind v4 utility classes + CSS Modules (existing per-component pattern), plain CSS custom properties/animations, no new npm dependencies.

## Global Constraints

- No test suite exists in this repo; verification is `npm run typecheck`, `npm run lint`, `npm run build` (catches broken links per `onBrokenLinks: "throw"`), and manual visual checks via `npm run start` in both `light`/`dark` themes, desktop + mobile widths, and with OS "reduce motion" enabled.
- No new UI/animation library dependency (no framer-motion, no gsap) — use `IntersectionObserver`, `requestAnimationFrame`, and CSS `@keyframes` only.
- Follow existing per-file indentation: tab-indented CSS Modules (`CategoryGrid/styles.module.css`, `CategoryCard/styles.module.css`), 2-space `src/css/custom.css` and `src/pages/index.module.css`.
- Use existing path aliases (`@components`, `@css`, `@lib`, `@theme`) rather than relative `../../..` paths, per `jsconfig.json` / `webpack-alias.js`.
- Respect `prefers-reduced-motion: reduce` for every new animation (disable animation, show end state immediately) — matches the existing pattern in `CategoryCard/styles.module.css`.
- Use only existing brand CSS variables (`--brand-primary*`, `--brand-accent*`, `--brand-bg-start/end`) defined in `src/css/custom.css` — do not invent new colors.

---

### Task 1: Categories title gradient text

**Files:**
- Modify: `src/components/CategoryGrid/styles.module.css:19-25` (`.sectionTitle`), `:44-47` (light override)

**Interfaces:**
- Consumes: existing `--brand-primary`, `--brand-primary-light`, `--brand-primary-dark`, `--brand-accent`, `--brand-accent-light` CSS vars (already defined in `src/css/custom.css`).
- Produces: no change to the `.sectionTitle` class name or its consumer in `CategoryGrid/index.tsx` — visual-only change.

- [ ] **Step 1: Replace the solid-color title styling with the hero's gradient-text technique**

Edit `src/components/CategoryGrid/styles.module.css`. Replace:

```css
.sectionTitle {
	position: relative;
	display: inline-block;
	padding-bottom: 0.55rem;
	color: #f7f2ff;
	text-shadow: 0 8px 22px rgb(0 0 0 / 0.18);
}
```

with:

```css
.sectionTitle {
	position: relative;
	display: inline-block;
	padding-bottom: 0.55rem;
	background: linear-gradient(
		to right,
		var(--brand-primary-light),
		var(--brand-accent-light),
		var(--brand-primary)
	);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	background-clip: text;
}
```

and replace:

```css
html[data-theme="light"] .sectionTitle {
	color: #2f2344;
	text-shadow: none;
}
```

with:

```css
html[data-theme="light"] .sectionTitle {
	background: linear-gradient(
		to right,
		var(--brand-primary-dark),
		var(--brand-accent),
		var(--brand-primary)
	);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	background-clip: text;
}
```

Leave `.sectionTitle::after` and its light-mode override untouched — the gradient underline stays as-is.

- [ ] **Step 2: Verify in the browser**

Run `npm run start`, open the homepage, and confirm the "Categories" heading now renders with the same left-to-right purple→coral gradient fill as the "My Knowledge Base" hero title, in both light and dark theme, and the underline bar is still visible beneath it.

- [ ] **Step 3: Commit**

```bash
git add src/components/CategoryGrid/styles.module.css
git commit -m "style: match Categories title to hero gradient text"
```

---

### Task 2: Unify navbar GitHub icon and theme-toggle icon color/centering

**Files:**
- Modify: `src/css/custom.css:375-422` (`.header-github-link` block), `:634-647` (`.navbar [class*='toggleButton']` block)

**Interfaces:**
- Consumes: existing `--brand-primary-dark`, `--brand-primary-darkest`, `--brand-primary-lightest` vars.
- Produces: no class renames; both `.header-github-link` and `.navbar [class*='toggleButton']` keep their selectors.

- [ ] **Step 1: Make the GitHub icon reference the same color variables as the toggle button**

In `src/css/custom.css`, change the base `.header-github-link` color from `var(--ifm-navbar-link-color)` to `var(--brand-primary-dark)`:

```css
.header-github-link {
  width: 2.65rem;
  height: 2.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgb(var(--brand-primary-rgb) / 0.14);
  background: rgb(var(--brand-primary-rgb) / 0.06);
  color: var(--brand-primary-dark);
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease;
}
```

Change its hover color from `var(--brand-primary-dark)` to `var(--brand-primary-darkest)`, matching the toggle button's hover:

```css
.header-github-link:hover {
  transform: translateY(-1px);
  border-color: rgb(var(--brand-primary-rgb) / 0.24);
  background: rgb(var(--brand-primary-rgb) / 0.12);
  color: var(--brand-primary-darkest);
  box-shadow: 0 12px 24px rgb(var(--brand-primary-rgb) / 0.12);
}
```

The `[data-theme='dark'] .header-github-link` and `:hover` blocks already use `var(--brand-primary-lightest)`, matching the toggle button's dark-mode colors — leave those two blocks unchanged.

- [ ] **Step 2: Make the toggle button explicitly center its icon, like the GitHub link does**

Add `display: flex; align-items: center; justify-content: center;` to `.navbar [class*='toggleButton']`:

```css
.navbar [class*='toggleButton'] {
  width: 2.65rem;
  height: 2.65rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(var(--brand-primary-rgb) / 0.14);
  border-radius: 999px;
  background: rgb(var(--brand-primary-rgb) / 0.06);
  color: var(--brand-primary-dark);
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease;
}
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start`. In both light and dark theme, compare the GitHub icon and the sun/moon toggle icon in the top-right of the navbar: they should render in the exact same purple shade at rest, the same darker/lighter shade on hover, and both glyphs should sit visually centered inside their circular buttons at the same vertical position.

- [ ] **Step 4: Commit**

```bash
git add src/css/custom.css
git commit -m "style: unify navbar GitHub/theme-toggle icon color and centering"
```

---

### Task 3: Category card glow-border-pulse hover effect

**Files:**
- Modify: `src/components/CategoryCard/styles.module.css:24-27` (`.categoryCard:hover`), `:60-153` (each `.card-{color}` variant), `:49-58` (reduced-motion block)

**Interfaces:**
- Consumes: existing `--brand-primary-rgb`, `--brand-accent-rgb` vars.
- Produces: new `--glow-rgb` custom property set per `.card-{color}` variant, consumed by the new `glowPulse` keyframes on `.categoryCard:hover`.

- [ ] **Step 1: Add a `--glow-rgb` custom property to each color variant**

In `src/components/CategoryCard/styles.module.css`, add one declaration to each of the five dark-mode variant blocks (purple/blue/cyan/green/pink), e.g. for purple:

```css
/* Dark mode - Purple card */
.card-purple {
	--glow-rgb: var(--brand-primary-rgb);
	background: linear-gradient(
		135deg,
		rgb(var(--brand-primary-rgb) / 0.3),
		rgb(var(--brand-accent-rgb) / 0.2)
	);
	border-color: rgb(var(--brand-primary-rgb) / 0.22);
}
```

Use this mapping (matching each variant's dominant hue already used in its own background gradient):

| Variant | `--glow-rgb` |
|---|---|
| `.card-purple` | `var(--brand-primary-rgb)` |
| `.card-blue` | `var(--brand-primary-rgb)` |
| `.card-cyan` | `var(--brand-accent-rgb)` |
| `.card-green` | `var(--brand-primary-rgb)` |
| `.card-pink` | `var(--brand-accent-rgb)` |

Add the same `--glow-rgb: ...;` line as the first declaration inside each of the five `.card-{color}` blocks only (not their `:hover` or light-mode override blocks — the light-mode overrides inherit the dark block's custom property since they share the same selector class).

- [ ] **Step 2: Add the pulse keyframes and apply them on hover**

Replace:

```css
.categoryCard:hover {
	box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
	transform: translateY(-4px);
}
```

with:

```css
.categoryCard:hover {
	transform: translateY(-4px);
	animation: glowPulse 1.8s ease-in-out infinite;
}

@keyframes glowPulse {
	0%,
	100% {
		box-shadow:
			0 20px 50px rgba(0, 0, 0, 0.2),
			0 0 0 0 rgb(var(--glow-rgb, var(--brand-primary-rgb)) / 0.35);
	}
	50% {
		box-shadow:
			0 20px 50px rgba(0, 0, 0, 0.2),
			0 0 26px 4px rgb(var(--glow-rgb, var(--brand-primary-rgb)) / 0.45);
	}
}
```

- [ ] **Step 3: Disable the animation and show a static glow under reduced motion**

Replace the existing reduced-motion block:

```css
@media (prefers-reduced-motion: reduce) {
	.categoryCard {
		opacity: 1;
		animation: none;
	}

	.categoryCard:hover .cardIcon {
		transform: none;
	}
}
```

with:

```css
@media (prefers-reduced-motion: reduce) {
	.categoryCard {
		opacity: 1;
		animation: none;
	}

	.categoryCard:hover {
		animation: none;
		box-shadow:
			0 20px 50px rgba(0, 0, 0, 0.2),
			0 0 20px 3px rgb(var(--glow-rgb, var(--brand-primary-rgb)) / 0.4);
	}

	.categoryCard:hover .cardIcon {
		transform: none;
	}
}
```

- [ ] **Step 4: Verify in the browser**

Run `npm run start`, hover each of the five category cards on the homepage in both themes and confirm a soft glow pulses around the card border in that card's own hue (purple/blue/cyan/green/pink), on top of the existing lift/shadow/icon-rotate. Then enable OS "reduce motion" and confirm hovering shows a static (non-pulsing) glow instead.

- [ ] **Step 5: Commit**

```bash
git add src/components/CategoryCard/styles.module.css
git commit -m "style: add per-category glow pulse to category card hover"
```

---

### Task 4: Footer rich brand gradient

**Files:**
- Modify: `src/css/custom.css:679-696` (light and dark `.footer`/`.footer--dark` background rules)

**Interfaces:**
- Consumes: existing `--brand-primary`, `--brand-primary-light`, `--brand-accent`, `--brand-accent-light`, `--brand-bg-start`, `--brand-bg-end` vars.
- Produces: no selector/class changes, background value only.

- [ ] **Step 1: Replace the light-mode footer background**

Replace:

```css
[data-theme='light'] .footer.footer--dark {
  --ifm-footer-color: #3f3550;
  --ifm-footer-title-color: #22192f;
  --ifm-footer-link-color: #22192f;
  background: linear-gradient(180deg, #ebe3f2 0%, #cec3da 100%) !important;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.45);
```

with:

```css
[data-theme='light'] .footer.footer--dark {
  --ifm-footer-color: #3f3550;
  --ifm-footer-title-color: #22192f;
  --ifm-footer-link-color: #22192f;
  background: linear-gradient(
    180deg,
    rgb(var(--brand-primary-rgb) / 0.16) 0%,
    rgb(var(--brand-accent-rgb) / 0.14) 55%,
    var(--brand-bg-start) 100%
  ) !important;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.45);
```

(keep whatever closing properties/brace already follow this rule unchanged).

- [ ] **Step 2: Replace the dark-mode footer background**

Replace:

```css
[data-theme='dark'] .footer,
[data-theme='dark'] .footer--dark {
  background:
    linear-gradient(180deg, rgb(255 255 255 / 0.03), rgb(255 255 255 / 0)),
    #191524;
}
```

with:

```css
[data-theme='dark'] .footer,
[data-theme='dark'] .footer--dark {
  background:
    linear-gradient(180deg, rgb(255 255 255 / 0.04), rgb(255 255 255 / 0) 40%),
    linear-gradient(
      160deg,
      var(--brand-bg-end) 0%,
      color-mix(in srgb, var(--brand-accent) 12%, var(--brand-bg-end)) 55%,
      var(--brand-bg-start) 100%
    );
}
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start`, scroll to the footer in both light and dark theme, and confirm it now shows a visible purple→coral gradient (richer than the previous flat pale/near-solid tone) while footer text stays legible.

- [ ] **Step 4: Commit**

```bash
git add src/css/custom.css
git commit -m "style: richer brand gradient for footer background"
```

---

### Task 5: `ScrollReveal` component

**Files:**
- Create: `src/components/ScrollReveal/index.tsx`
- Create: `src/components/ScrollReveal/styles.module.css`

**Interfaces:**
- Produces: `export default function ScrollReveal({ children, className }: { children: ReactNode; className?: string }): ReactNode` — a `<div>` wrapper that fades/slides its children in once when it enters the viewport.
- Consumed by: Task 6 (homepage sections), Task 7 (`StatsSection`, via the same wrapper).

- [ ] **Step 1: Implement the component**

Create `src/components/ScrollReveal/styles.module.css`:

```css
.reveal {
	opacity: 0;
	transform: translateY(16px);
	transition:
		opacity 500ms ease-out,
		transform 500ms ease-out;
}

.revealVisible {
	opacity: 1;
	transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
	.reveal {
		opacity: 1;
		transform: none;
		transition: none;
	}
}
```

Create `src/components/ScrollReveal/index.tsx`:

```tsx
import { cn } from "@lib/utils";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
}

export default function ScrollReveal({
  children,
  className,
}: ScrollRevealProps): ReactNode {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) {
      return;
    }

    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={cn(styles.reveal, visible && styles.revealVisible, className)}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Verify with typecheck**

Run `npm run typecheck` — expect no new errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/ScrollReveal
git commit -m "feat: add ScrollReveal component for scroll-in animations"
```

---

### Task 6: Apply `ScrollReveal` to homepage sections

**Files:**
- Modify: `src/pages/index.tsx`

**Interfaces:**
- Consumes: `ScrollReveal` from Task 5 (`import ScrollReveal from "@components/ScrollReveal"`).

- [ ] **Step 1: Wrap `HomeIntro`, `RecentDocs`, and the categories block**

In `src/pages/index.tsx`, add the import:

```tsx
import ScrollReveal from "@components/ScrollReveal";
```

Wrap the three sections below the hero (leave the hero `GlassCard` itself unwrapped — it should render immediately, not on scroll):

```tsx
          <ScrollReveal>
            <HomeIntro />
          </ScrollReveal>
          <ScrollReveal>
            <RecentDocs />
          </ScrollReveal>

          {/* Categories Section - Same Gradient */}
          <ScrollReveal>
            <div className="pb-16 md:pb-20">
              <GlassCard>
                <CategoryGrid />
              </GlassCard>
            </div>
          </ScrollReveal>
```

(This replaces the existing unwrapped `<HomeIntro />`, `<RecentDocs />`, and categories `<div>` block — the `StatsSection` from Task 7 will be inserted between `HomeIntro` and `RecentDocs` in that task, also wrapped.)

- [ ] **Step 2: Verify in the browser**

Run `npm run start`, reload the homepage, and scroll down slowly: the intro strip, recent-docs grid, and categories block should each fade/slide into view as they cross into the viewport, rather than all appearing instantly on load. Reload with OS "reduce motion" on and confirm everything is visible immediately with no animation.

- [ ] **Step 3: Commit**

```bash
git add src/pages/index.tsx
git commit -m "feat: reveal homepage sections on scroll"
```

---

### Task 7: `StatsSection` homepage component with count-up

**Files:**
- Create: `src/components/StatsSection/index.tsx`
- Create: `src/components/StatsSection/styles.module.css`
- Create: `src/hooks/useCountUp.ts`
- Modify: `src/pages/index.tsx`

**Interfaces:**
- Produces: `export function useCountUp(target: number, options?: { durationMs?: number }): number` in `src/hooks/useCountUp.ts` — returns the current animated value, starting at `0` and easing to `target` over `durationMs` (default `1200`) once called; immediately returns `target` under reduced motion.
- Produces: `export default function StatsSection(): ReactNode | null` in `src/components/StatsSection/index.tsx`.
- Consumes: `useAllDocsData` from `@docusaurus/plugin-content-docs/client` (same API `CategoryGrid` already uses) and the `CategoryGrid`-style `useThemeConfig().navbar.items` filter, to avoid re-deriving category logic from scratch.

- [ ] **Step 1: Write the count-up hook**

Create `src/hooks/useCountUp.ts`:

```ts
import { useEffect, useRef, useState } from "react";

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

export function useCountUp(
  target: number,
  { durationMs = 1200 }: { durationMs?: number } = {},
): number {
  const [value, setValue] = useState(prefersReducedMotion() ? target : 0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setValue(target);
      return;
    }

    const start = performance.now();

    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      const eased = 1 - (1 - progress) ** 3;
      setValue(Math.round(eased * target));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [target, durationMs]);

  return value;
}
```

- [ ] **Step 2: Write the stats-derivation + component**

Create `src/components/StatsSection/styles.module.css`:

```css
.stats {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	gap: 1.5rem;
	text-align: center;
}

.statValue {
	font-size: 2.5rem;
	font-weight: 800;
	line-height: 1;
	background: linear-gradient(
		to right,
		var(--brand-primary-light),
		var(--brand-accent-light),
		var(--brand-primary)
	);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	background-clip: text;
}

html[data-theme="light"] .statValue {
	background: linear-gradient(
		to right,
		var(--brand-primary-dark),
		var(--brand-accent),
		var(--brand-primary)
	);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	background-clip: text;
}

.statLabel {
	margin-top: 0.35rem;
	font-size: 0.85rem;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.14em;
	color: #cbd5e1;
}

html[data-theme="light"] .statLabel {
	color: #475569;
}
```

Create `src/components/StatsSection/index.tsx`. `useAllDocsData()` returns, per plugin instance, a `GlobalVersion` with a flat `docs: GlobalDoc[]` array covering every doc page in that version (this is a different, flatter field than the `sidebars` map `CategoryGrid` uses for hrefs) — use its `.length` directly for the doc count, no recursion needed:

```tsx
import { useAllDocsData } from "@docusaurus/plugin-content-docs/client";
import { useThemeConfig } from "@docusaurus/theme-common";
import { useCountUp } from "@/hooks/useCountUp";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

function StatCard({ value, label }: { value: number; label: string }) {
  const animated = useCountUp(value);
  return (
    <div>
      <div className={styles.statValue}>{animated}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  );
}

export default function StatsSection(): ReactNode | null {
  const navbarItems = useThemeConfig().navbar.items;
  const categoryCount = navbarItems.filter(
    (item) =>
      item.type === "doc" ||
      item.type === "docSidebar" ||
      item.type === "docsVersion",
  ).length;

  const allDocsData = useAllDocsData();
  const defaultDocsData = allDocsData.default ?? Object.values(allDocsData)[0];
  const docCount = defaultDocsData?.versions[0]?.docs.length ?? 0;

  if (categoryCount === 0 && docCount === 0) {
    return null;
  }

  return (
    <section className="mx-auto mb-10 w-full max-w-5xl">
      <div className={styles.stats}>
        <StatCard value={categoryCount} label="Categories" />
        <StatCard value={docCount} label="Documented topics" />
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Wire it into the homepage, between `HomeIntro` and `RecentDocs`**

In `src/pages/index.tsx`, add the import:

```tsx
import StatsSection from "@components/StatsSection";
```

and insert it, wrapped in `ScrollReveal` (from Task 6), between the `HomeIntro` and `RecentDocs` reveals:

```tsx
          <ScrollReveal>
            <HomeIntro />
          </ScrollReveal>
          <ScrollReveal>
            <StatsSection />
          </ScrollReveal>
          <ScrollReveal>
            <RecentDocs />
          </ScrollReveal>
```

- [ ] **Step 4: Verify in the browser**

Run `npm run start`, load the homepage, and scroll to the stats row: confirm both numbers animate up from 0 to their final counts once the row scrolls into view, the count matches the real number of categories (5, per the navbar) and real total doc pages (cross-check by counting sidebar entries in `docs/`), and reduced-motion shows the final numbers immediately with no animation.

- [ ] **Step 5: Commit**

```bash
git add src/components/StatsSection src/hooks/useCountUp.ts src/pages/index.tsx
git commit -m "feat: add animated stats section to homepage"
```

---

### Task 8: Docs admonitions + code block chrome polish

**Files:**
- Modify: `src/css/custom.css` (append new rules near the existing `/* ============ Global Styles ============ */` markdown section, after the table/pagination rules around line 1082)

**Interfaces:**
- Consumes: existing `--brand-primary-rgb`, `--brand-accent-rgb`, `--brand-primary`, `--brand-accent` vars; targets Docusaurus's default admonition/Prism DOM classes (`.theme-admonition`, `.theme-admonition-{type}`, `[class*='codeBlockContainer_']`), no new components.

- [ ] **Step 1: Add refined admonition styling**

Append to `src/css/custom.css`:

```css
/* ============ Admonitions ============ */
.theme-admonition {
  border-radius: 0.75rem;
  border-width: 1px;
  border-left-width: 4px;
  box-shadow: 0 8px 20px rgb(0 0 0 / 0.06);
}

[data-theme='dark'] .theme-admonition {
  box-shadow: 0 8px 20px rgb(0 0 0 / 0.25);
}

.theme-admonition-note,
.theme-admonition-info {
  border-left-color: var(--brand-primary);
  background: rgb(var(--brand-primary-rgb) / 0.06);
}

.theme-admonition-tip {
  border-left-color: var(--brand-accent);
  background: rgb(var(--brand-accent-rgb) / 0.06);
}

[data-theme='dark'] .theme-admonition-note,
[data-theme='dark'] .theme-admonition-info {
  background: rgb(var(--brand-primary-rgb) / 0.1);
}

[data-theme='dark'] .theme-admonition-tip {
  background: rgb(var(--brand-accent-rgb) / 0.1);
}
```

- [ ] **Step 2: Add a subtle top accent to code blocks**

Append:

```css
/* ============ Code blocks ============ */
[class*='codeBlockContainer_'] {
  border-top: 2px solid rgb(var(--brand-primary-rgb) / 0.35);
  border-radius: var(--ifm-code-border-radius);
  overflow: hidden;
}

[class*='codeBlockTitle_'] {
  border-bottom: 1px solid rgb(var(--brand-primary-rgb) / 0.16);
  font-weight: 600;
}
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start`, open a doc page that has `:::note`/`:::tip` admonitions and fenced code blocks (e.g. anything under `docs/programming/`), and confirm admonitions show a colored left border + soft background tint per type, and code blocks show a thin brand-colored top accent, in both themes.

- [ ] **Step 4: Commit**

```bash
git add src/css/custom.css
git commit -m "style: polish admonitions and code block chrome on doc pages"
```

---

### Task 9: Reading time + scroll progress bar on doc pages

**Files:**
- Create: `src/components/ReadingProgress/index.tsx`
- Create: `src/components/ReadingProgress/styles.module.css`
- Modify: `src/theme/DocItem/Layout/index.js`
- Modify: `src/theme/DocItem/Layout/styles.module.css`

**Interfaces:**
- Produces: `export default function ReadingProgress({ targetRef }: { targetRef: RefObject<HTMLElement | null> }): ReactNode` — renders a fixed top progress bar that fills based on how much of `targetRef`'s element has been scrolled past, and a `~N min read` badge is derived separately (see Step 2) and rendered by the caller.
- Consumes: rendered inside `DocItemLayout` (`src/theme/DocItem/Layout/index.js`), wrapping the existing `<article>` content with a `ref`.

- [ ] **Step 1: Write the progress bar component**

Create `src/components/ReadingProgress/styles.module.css`:

```css
.progressTrack {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 3px;
	z-index: 1001;
	background: transparent;
	pointer-events: none;
}

.progressFill {
	height: 100%;
	width: 0%;
	background: linear-gradient(
		90deg,
		var(--brand-primary),
		var(--brand-accent),
		var(--brand-primary-light)
	);
	transition: width 120ms ease-out;
}

@media (prefers-reduced-motion: reduce) {
	.progressFill {
		transition: none;
	}
}
```

Create `src/components/ReadingProgress/index.tsx`:

```tsx
import { useEffect, useState } from "react";
import type { ReactNode, RefObject } from "react";
import styles from "./styles.module.css";

interface ReadingProgressProps {
  targetRef: RefObject<HTMLElement | null>;
}

export default function ReadingProgress({
  targetRef,
}: ReadingProgressProps): ReactNode {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const node = targetRef.current;
      if (!node) {
        return;
      }
      const rect = node.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      if (total <= 0) {
        setProgress(100);
        return;
      }
      const scrolled = Math.min(Math.max(-rect.top, 0), total);
      setProgress((scrolled / total) * 100);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  }, [targetRef]);

  return (
    <div className={styles.progressTrack}>
      <div className={styles.progressFill} style={{ width: `${progress}%` }} />
    </div>
  );
}
```

- [ ] **Step 2: Wire the progress bar and a reading-time label into `DocItem/Layout`**

Modify `src/theme/DocItem/Layout/index.js`:

```js
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useWindowSize } from "@docusaurus/theme-common";
import ReadingProgress from "@components/ReadingProgress";
import ContentVisibility from "@theme/ContentVisibility";
import DocBreadcrumbs from "@theme/DocBreadcrumbs";
import DocItemContent from "@theme/DocItem/Content";
import DocItemFooter from "@theme/DocItem/Footer";
import DocItemPaginator from "@theme/DocItem/Paginator";
import DocItemTOCDesktop from "@theme/DocItem/TOC/Desktop";
import DocItemTOCMobile from "@theme/DocItem/TOC/Mobile";
import DocVersionBadge from "@theme/DocVersionBadge";
import DocVersionBanner from "@theme/DocVersionBanner";
import clsx from "clsx";
import { useRef, useState, useEffect } from "react";
import styles from "./styles.module.css";

/**
 * Decide if the toc should be rendered, on mobile or desktop viewports
 */
function useDocTOC() {
  const { frontMatter, toc } = useDoc();
  const windowSize = useWindowSize();
  const hidden = frontMatter.hide_table_of_contents;
  const canRender = !hidden && toc.length > 0;
  const mobile = canRender ? <DocItemTOCMobile /> : undefined;
  const desktop =
    canRender && (windowSize === "desktop" || windowSize === "ssr") ? (
      <DocItemTOCDesktop />
    ) : undefined;
  return {
    hidden,
    mobile,
    desktop,
  };
}

function useReadingTime(articleRef) {
  const [minutes, setMinutes] = useState(null);

  useEffect(() => {
    const node = articleRef.current;
    if (!node) {
      return;
    }
    const words = node.innerText.trim().split(/\s+/).filter(Boolean).length;
    setMinutes(Math.max(1, Math.round(words / 200)));
  }, [articleRef]);

  return minutes;
}

export default function DocItemLayout({ children }) {
  const docTOC = useDocTOC();
  const { metadata } = useDoc();
  const articleRef = useRef(null);
  const readingMinutes = useReadingTime(articleRef);
  return (
    <div className="row">
      <ReadingProgress targetRef={articleRef} />
      <div
        className={clsx("col", "xl:px-10", !docTOC.hidden && styles.docItemCol)}
      >
        <ContentVisibility metadata={metadata} />
        <DocVersionBanner />
        <div className={styles.docItemContainer}>
          <article ref={articleRef}>
            <DocBreadcrumbs />
            {readingMinutes !== null && (
              <p className={styles.readingTime}>{readingMinutes} min read</p>
            )}
            <DocVersionBadge />
            {docTOC.mobile}
            <DocItemContent>{children}</DocItemContent>
            <div className={styles.docFooterMetaHidden}>
              <DocItemFooter />
            </div>
          </article>
          <DocItemPaginator />
        </div>
      </div>
      {docTOC.desktop && <div className="col col--3">{docTOC.desktop}</div>}
    </div>
  );
}
```

Add the `.readingTime` style to `src/theme/DocItem/Layout/styles.module.css`:

```css
.readingTime {
	margin: 0 0 0.75rem;
	font-size: 0.8rem;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.12em;
	color: rgb(var(--brand-primary-rgb) / 0.75);
}
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start`, open any doc page, and confirm: a thin gradient progress bar appears fixed at the very top of the viewport and fills up as you scroll through the article; a "N min read" label appears above the title, right below the breadcrumbs; scrolling to the bottom brings the bar to (or near) 100%.

- [ ] **Step 4: Commit**

```bash
git add src/components/ReadingProgress src/theme/DocItem/Layout
git commit -m "feat: add reading time and scroll progress bar to doc pages"
```

---

### Task 10: TOC active-item gradient indicator

**Files:**
- Modify: `src/css/custom.css:1039-1047` (`.table-of-contents__link--active` rules)

**Interfaces:**
- Consumes: existing `--brand-primary`, `--brand-accent`, `--brand-primary-light` vars.

- [ ] **Step 1: Replace the flat active-background with a left gradient bar**

Replace:

```css
[data-theme="light"] .table-of-contents a.table-of-contents__link--active {
  background: rgb(var(--brand-primary-rgb) / 0.12);
  color: var(--brand-primary-darkest);
}
```

with:

```css
[data-theme="light"] .table-of-contents a.table-of-contents__link--active {
  background: rgb(var(--brand-primary-rgb) / 0.12);
  color: var(--brand-primary-darkest);
  border-left: 2px solid transparent;
  border-image: linear-gradient(
    180deg,
    var(--brand-primary-dark),
    var(--brand-accent)
  );
  border-image-slice: 1;
}
```

and replace:

```css
[data-theme="dark"] .table-of-contents a.table-of-contents__link--active {
  background: rgb(var(--brand-primary-rgb) / 0.22);
  color: var(--brand-primary-lightest);
}
```

with:

```css
[data-theme="dark"] .table-of-contents a.table-of-contents__link--active {
  background: rgb(var(--brand-primary-rgb) / 0.22);
  color: var(--brand-primary-lightest);
  border-left: 2px solid transparent;
  border-image: linear-gradient(
    180deg,
    var(--brand-primary-light),
    var(--brand-accent-light)
  );
  border-image-slice: 1;
}
```

- [ ] **Step 2: Verify in the browser**

Run `npm run start`, open a doc page with multiple headings, scroll through it, and confirm the currently-active TOC entry (right sidebar) shows a small vertical gradient bar on its left edge instead of a flat highlight only.

- [ ] **Step 3: Commit**

```bash
git add src/css/custom.css
git commit -m "style: gradient active indicator for doc TOC"
```

---

### Task 11: Back-to-top button

**Files:**
- Create: `src/components/BackToTop/index.tsx`
- Create: `src/components/BackToTop/styles.module.css`
- Create: `src/theme/Root/index.js`

**Interfaces:**
- Produces: `export default function BackToTop(): ReactNode` in `src/components/BackToTop/index.tsx`.
- Produces: `export default function Root({ children })` in `src/theme/Root/index.js`, the standard Docusaurus `Root` theme swizzle slot (none exists yet in this repo), rendering `children` plus `<BackToTop />` once, site-wide.

- [ ] **Step 1: Write the button component**

Create `src/components/BackToTop/styles.module.css`:

```css
.button {
	position: fixed;
	right: 1.5rem;
	bottom: 1.5rem;
	z-index: 999;
	width: 2.65rem;
	height: 2.65rem;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 999px;
	border: 1px solid rgb(var(--brand-primary-rgb) / 0.14);
	background: rgb(var(--brand-primary-rgb) / 0.9);
	color: white;
	box-shadow: 0 12px 24px rgb(var(--brand-primary-rgb) / 0.28);
	cursor: pointer;
	opacity: 0;
	pointer-events: none;
	transform: translateY(8px);
	transition:
		opacity 200ms ease,
		transform 200ms ease,
		background-color 180ms ease;
}

.buttonVisible {
	opacity: 1;
	pointer-events: auto;
	transform: translateY(0);
}

.button:hover {
	background: rgb(var(--brand-primary-rgb) / 1);
	transform: translateY(-2px);
}

@media (prefers-reduced-motion: reduce) {
	.button {
		transition: opacity 200ms ease;
	}
}
```

Create `src/components/BackToTop/index.tsx`:

```tsx
import { cn } from "@lib/utils";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

export default function BackToTop(): ReactNode {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > 600);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <button
      type="button"
      aria-label="Back to top"
      className={cn(styles.button, visible && styles.buttonVisible)}
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
    >
      ↑
    </button>
  );
}
```

- [ ] **Step 2: Mount it once, site-wide, via a `Root` swizzle**

Create `src/theme/Root/index.js`:

```js
import BackToTop from "@components/BackToTop";
import React from "react";

export default function Root({ children }) {
  return (
    <>
      {children}
      <BackToTop />
    </>
  );
}
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start`. On the homepage and on a doc page, confirm the button is hidden near the top of the page, appears (bottom-right) after scrolling down ~600px, and clicking it smooth-scrolls back to the top and then hides itself again.

- [ ] **Step 4: Commit**

```bash
git add src/components/BackToTop src/theme/Root
git commit -m "feat: add site-wide back-to-top button"
```

---

### Task 12: Cursor glow on hero and categories sections

**Files:**
- Create: `src/components/CursorGlow/index.tsx`
- Create: `src/components/CursorGlow/styles.module.css`
- Modify: `src/pages/index.tsx`

**Interfaces:**
- Produces: `export default function CursorGlow(): ReactNode | null` — renders `null` on touch/coarse-pointer devices or under reduced motion; otherwise renders a fixed, pointer-events-none glow `<div>` that follows the mouse while it is over the nearest positioned ancestor.
- Consumed by: `src/pages/index.tsx`, mounted once inside the existing `.heroGradient` wrapper (which is already `position: relative`), so its `position: absolute` glow tracks mouse movement within that whole wrapper (hero + categories, since both live inside it — see `index.tsx`'s structure).

- [ ] **Step 1: Write the component**

Create `src/components/CursorGlow/styles.module.css`:

```css
.glow {
	position: absolute;
	top: 0;
	left: 0;
	width: 480px;
	height: 480px;
	margin-left: -240px;
	margin-top: -240px;
	border-radius: 50%;
	background: radial-gradient(
		circle,
		rgb(var(--brand-primary-rgb) / 0.18),
		transparent 70%
	);
	pointer-events: none;
	z-index: 0;
	opacity: 0;
	transition: opacity 300ms ease;
	will-change: transform;
}

.glowVisible {
	opacity: 1;
}

@media (hover: none), (pointer: coarse) {
	.glow {
		display: none;
	}
}
```

Create `src/components/CursorGlow/index.tsx`:

```tsx
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

export default function CursorGlow(): ReactNode | null {
  const glowRef = useRef<HTMLDivElement>(null);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const coarsePointer = window.matchMedia(
      "(hover: none), (pointer: coarse)",
    ).matches;
    setSupported(!reducedMotion && !coarsePointer);
  }, []);

  useEffect(() => {
    if (!supported) {
      return;
    }

    const parent = glowRef.current?.parentElement;
    if (!parent) {
      return;
    }

    const handleMove = (event: MouseEvent) => {
      const rect = parent.getBoundingClientRect();
      const node = glowRef.current;
      if (!node) {
        return;
      }
      node.style.transform = `translate(${event.clientX - rect.left}px, ${
        event.clientY - rect.top
      }px)`;
      node.classList.add(styles.glowVisible);
    };

    const handleLeave = () => {
      glowRef.current?.classList.remove(styles.glowVisible);
    };

    parent.addEventListener("mousemove", handleMove);
    parent.addEventListener("mouseleave", handleLeave);
    return () => {
      parent.removeEventListener("mousemove", handleMove);
      parent.removeEventListener("mouseleave", handleLeave);
    };
  }, [supported]);

  if (!supported) {
    return null;
  }

  return <div ref={glowRef} className={styles.glow} />;
}
```

- [ ] **Step 2: Mount it in the homepage hero wrapper**

In `src/pages/index.tsx`, add the import:

```tsx
import CursorGlow from "@components/CursorGlow";
```

Render it as the first child inside the existing `.heroGradient` wrapper div (which already has `position: relative` via the `relative` Tailwind class), right after the opening tag and before the floating blob elements:

```tsx
      <div
        className={clsx(styles.heroGradient, "relative w-full overflow-hidden")}
      >
        <CursorGlow />
        {/* Animated background elements */}
        <div className={clsx(styles.heroBlob, styles.heroBlobPrimary)} />
```

- [ ] **Step 3: Verify in the browser**

Run `npm run start` on a desktop browser (mouse, not touch emulation), move the mouse over the hero and categories sections on the homepage, and confirm a soft purple glow follows the cursor smoothly and fades out when the mouse leaves that wrapper. Then check with the browser's device-toolbar touch emulation (or on an actual touch device) that no glow element renders, and confirm it's absent with OS "reduce motion" enabled too.

- [ ] **Step 4: Commit**

```bash
git add src/components/CursorGlow src/pages/index.tsx
git commit -m "feat: add cursor glow effect to homepage hero and categories"
```

---

## Final verification (after all tasks)

- [ ] Run `npm run typecheck`, `npm run lint`, and `npm run build` — all must pass cleanly (a broken internal link or type error fails the build per `onBrokenLinks: "throw"`).
- [ ] Run `npm run serve` and manually click through the homepage and at least one doc page in both light and dark theme, at a mobile width (~375px) and desktop width, confirming every change in this plan renders as described in its task's verification step.
