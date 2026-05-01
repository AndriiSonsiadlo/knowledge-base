# Midnight Coral Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the Docusaurus site with the Midnight Coral palette, heading-only display typography, a git-driven recent-docs homepage feed, a personal intro strip, and a more polished animated hero.

**Architecture:** Keep the redesign incremental and local to the existing Docusaurus structure. Add one small content plugin to expose recent-doc metadata through Docusaurus global data, add two homepage-only presentational components, and migrate existing hardcoded purple styling to a small set of CSS custom properties so the site theme can be adjusted without touching every component again.

**Tech Stack:** Docusaurus 3.9, React 19, TypeScript/TSX, plain CSS/CSS modules, Tailwind v4 utilities, Biome, `@fontsource/space-grotesk`.

## Global Constraints

- Node version floor is `>=20.0` (`package.json`).
- There is no unit-test suite in this repo; the red/green loop here is `npm run typecheck`, `npm run lint`, and especially `npm run build` because `onBrokenLinks: "throw"` fails the build on bad links.
- Use Biome formatting conventions (2-space indent in repo-managed files).
- Do not add a new animation library or UI framework.
- The recent-docs feed must use real git-derived `lastUpdatedAt` metadata, not hand-authored dates or manual curation.
- `showLastUpdateTime: true` must be enabled for docs metadata, but the default per-doc “Last updated” UI must stay hidden on doc pages.
- Body copy keeps the existing system font stack; `Space Grotesk` is headings/hero text only.

---

### Task 1: Add recent-docs metadata plumbing

**Files:**
- Create: `src/plugins/recent-docs-plugin.js`
- Modify: `docusaurus.config.js`
- Modify: `src/theme/DocItem/Layout/index.js`
- Modify: `src/theme/DocItem/Layout/styles.module.css`

**Interfaces:**
- Produces: plugin global data under `usePluginData("recent-docs-plugin")` with shape:

```ts
interface RecentDocSummary {
  title: string;
  description?: string;
  permalink: string;
  lastUpdatedAt: number;
}

interface RecentDocsPluginData {
  docs: RecentDocSummary[];
}
```

- Consumes: docs metadata from `allContent["docusaurus-plugin-content-docs"]?.default.loadedVersions[].docs[]`.

- [ ] **Step 1: Create the plugin file**

```js
module.exports = function recentDocsPlugin(_context, options = {}) {
  return {
    name: "recent-docs-plugin",
    async allContentLoaded({ allContent, actions }) {
      const docsContent = allContent["docusaurus-plugin-content-docs"]?.default;
      if (!docsContent) {
        actions.setGlobalData({ docs: [] });
        return;
      }

      const docs = docsContent.loadedVersions
        .flatMap((version) => version.docs)
        .filter((doc) => !doc.unlisted && !doc.draft && doc.lastUpdatedAt)
        .sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt)
        .slice(0, options.limit ?? 6)
        .map((doc) => ({
          title: doc.title,
          description: doc.description,
          permalink: doc.permalink,
          lastUpdatedAt: doc.lastUpdatedAt,
        }));

      actions.setGlobalData({ docs });
    },
  };
};
```

- [ ] **Step 2: Register the plugin and docs metadata source**

In `docusaurus.config.js`, update the classic docs preset:

```js
        docs: {
          sidebarPath: "./sidebars.js",
          showLastUpdateTime: true,
          editUrl:
            "https://github.com/AndriiSonsiadlo/knowledge-base/tree/master/",
        },
```

Then register the plugin in the `plugins` array next to the other local plugins:

```js
    ["./src/plugins/recent-docs-plugin.js", { limit: 6 }],
```

- [ ] **Step 3: Hide the default doc-page updated footer UI without breaking metadata**

Wrap the footer in a classed container in `src/theme/DocItem/Layout/index.js`:

```jsx
            <div className={styles.docFooterMetaHidden}>
              <DocItemFooter />
            </div>
```

Then hide only the last-updated block in `src/theme/DocItem/Layout/styles.module.css`:

```css
.docFooterMetaHidden :global(article footer div[class*="lastUpdated"]) {
  display: none;
}
```

- [ ] **Step 4: Verify the metadata path works**

Run: `npm run build`

Expected: build succeeds, which proves the docs plugin still loads and the new plugin can read `lastUpdatedAt` data without throwing.

- [ ] **Step 5: Commit**

```bash
git add docusaurus.config.js src/plugins/recent-docs-plugin.js src/theme/DocItem/Layout/index.js src/theme/DocItem/Layout/styles.module.css
git commit -m "feat: add recent docs metadata"
```

---

### Task 2: Build the homepage intro and recent-docs sections

**Files:**
- Create: `src/components/HomeIntro/index.tsx`
- Create: `src/components/RecentDocs/index.tsx`
- Modify: `src/pages/index.tsx`

**Interfaces:**
- Consumes: `siteConfig.customFields.githubUrl as string`
- Consumes: `usePluginData("recent-docs-plugin") as RecentDocsPluginData`
- Produces: `HomeIntro(): ReactNode` and `RecentDocs(): ReactNode | null`

- [ ] **Step 1: Create the intro strip component**

```tsx
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import type { ReactNode } from "react";

export default function HomeIntro(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  const githubUrl = siteConfig.customFields?.githubUrl as string;

  return (
    <section className="mx-auto mb-10 w-full max-w-5xl">
      <div className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/70 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.06)] backdrop-blur-[20px] dark:bg-black/30 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <img
            src="img/logo.png"
            alt="Andrii Sonsiadlo"
            className="h-14 w-14 rounded-2xl border border-white/20 object-cover"
          />
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-[var(--brand-primary)]">
              Andrii Sonsiadlo
            </p>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              Software engineer — documenting what I learn about computer science and building things.
            </p>
          </div>
        </div>
        <Link
          to={githubUrl}
          className="inline-flex items-center justify-center rounded-full bg-[var(--brand-primary)] px-4 py-2 text-sm font-semibold text-white no-underline transition hover:bg-[var(--brand-primary-dark)]"
        >
          View GitHub
        </Link>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Create the recent-docs component**

```tsx
import Link from "@docusaurus/Link";
import usePluginData from "@docusaurus/useGlobalData";
import Heading from "@theme/Heading";
import type { ReactNode } from "react";

interface RecentDocSummary {
  title: string;
  description?: string;
  permalink: string;
  lastUpdatedAt: number;
}

function formatRelativeDate(timestamp: number): string {
  const diffMs = timestamp - Date.now();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (Math.abs(diffDays) < 30) return rtf.format(diffDays, "day");
  const diffMonths = Math.round(diffDays / 30);
  if (Math.abs(diffMonths) < 12) return rtf.format(diffMonths, "month");
  return rtf.format(Math.round(diffMonths / 12), "year");
}

export default function RecentDocs(): ReactNode | null {
  const pluginData = usePluginData("recent-docs-plugin") as { docs?: RecentDocSummary[] } | undefined;
  const docs = pluginData?.docs ?? [];

  if (docs.length === 0) {
    return null;
  }

  return (
    <section className="mx-auto w-full max-w-6xl pb-16 md:pb-20">
      <div className="mb-8 text-center">
        <Heading as="h2" className="font-display text-3xl md:text-4xl">
          Recently updated
        </Heading>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-700 dark:text-slate-300">
          The latest notes I’ve touched in this knowledge base.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {docs.map((doc) => (
          <Link
            key={doc.permalink}
            to={doc.permalink}
            className="rounded-3xl border border-white/10 bg-white/70 p-5 text-inherit no-underline shadow-[0_8px_32px_rgba(0,0,0,0.06)] transition hover:-translate-y-0.5 hover:border-[var(--brand-accent)]/40 dark:bg-black/30"
          >
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--brand-accent)]">
              Updated {formatRelativeDate(doc.lastUpdatedAt)}
            </p>
            <Heading as="h3" className="mb-2 text-xl">
              {doc.title}
            </Heading>
            {doc.description ? (
              <p className="m-0 text-sm text-slate-700 dark:text-slate-300">{doc.description}</p>
            ) : null}
          </Link>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Wire both sections into the homepage**

At the top of `src/pages/index.tsx` add:

```tsx
import HomeIntro from "@components/HomeIntro";
import RecentDocs from "@components/RecentDocs";
```

Then insert them between the hero card and the category grid:

```tsx
          <HomeIntro />
          <RecentDocs />
```

- [ ] **Step 4: Verify type safety**

Run: `npm run typecheck`

Expected: no type errors for `customFields.githubUrl`, `usePluginData`, or the new component imports.

- [ ] **Step 5: Commit**

```bash
git add src/components/HomeIntro/index.tsx src/components/RecentDocs/index.tsx src/pages/index.tsx
git commit -m "feat: add homepage intro and feed"
```

---

### Task 3: Introduce Midnight Coral tokens and heading typography

**Files:**
- Modify: `package.json`
- Modify: `src/css/custom.css`
- Modify: `src/components/GlassCard/index.tsx`
- Modify: `src/components/CategoryCard/styles.module.css`
- Modify: `src/components/CategoryGrid/index.tsx`
- Modify: `src/components/CategoryGrid/styles.module.css`
- Modify: `src/theme/Navbar/Logo/index.js`

**Interfaces:**
- Produces: CSS custom properties `--brand-primary`, `--brand-primary-dark`, `--brand-primary-light`, `--brand-accent`, `--brand-accent-light`, `--brand-bg-start`, `--brand-bg-end`, `--font-display`
- Consumes: existing components that currently hardcode `purple-*`, `blue-*`, or `rgba(168, 85, 247, ...)`

- [ ] **Step 1: Add the heading font dependency**

Install a mature version of the package:

```bash
npm install @fontsource/space-grotesk
```

Expected: `package.json` and lockfile update with `@fontsource/space-grotesk` added.

- [ ] **Step 2: Import the font and declare the brand tokens**

At the top of `src/css/custom.css`, add:

```css
@import "@fontsource/space-grotesk/500.css";
@import "@fontsource/space-grotesk/700.css";
```

Then replace the duplicated primary-color blocks with a single token source:

```css
:root {
  --brand-primary: #7c5cff;
  --brand-primary-dark: #6a46f0;
  --brand-primary-light: #a992ff;
  --brand-accent: #ff6b6b;
  --brand-accent-light: #ff8f8f;
  --brand-bg-start: #f8f6fb;
  --brand-bg-end: #fdeeee;
  --font-display: "Space Grotesk", var(--ifm-font-family-base);

  --ifm-color-primary: var(--brand-primary);
  --ifm-color-primary-dark: var(--brand-primary-dark);
  --ifm-color-primary-darker: #5b3ff0;
  --ifm-color-primary-darkest: #4b32d1;
  --ifm-color-primary-light: var(--brand-primary-light);
  --ifm-color-primary-lighter: #cbc0ff;
  --ifm-color-primary-lightest: #eee9ff;
  --docusaurus-highlighted-code-line-border-left-color: var(--brand-primary);
}

html[data-theme="dark"] {
  --brand-primary: #7c5cff;
  --brand-primary-dark: #5b3ff0;
  --brand-primary-light: #a992ff;
  --brand-accent: #ff6b6b;
  --brand-accent-light: #ff8f8f;
  --brand-bg-start: #120c1e;
  --brand-bg-end: #1d1330;
}
```

- [ ] **Step 3: Apply the display font only where the spec allows it**

In `src/css/custom.css`, add:

```css
.font-display,
.markdown h1,
.markdown h2,
.markdown h3 {
  font-family: var(--font-display);
}
```

Keep body text, nav text, sidebar text, and paragraph copy unchanged.

- [ ] **Step 4: Replace the remaining purple-specific styling with token-based styling**

Update the touched files so they reference `var(--brand-primary)` / `var(--brand-accent)` instead of `purple-*` and old purple RGBA values. The important concrete replacements are:

```css
[data-theme="light"] .markdown code {
  background: color-mix(in srgb, var(--brand-primary) 14%, white);
  color: color-mix(in srgb, var(--brand-primary-dark) 70%, black);
}

.markdown a {
  color: var(--brand-primary);
  text-decoration-color: var(--brand-accent);
}

.markdown blockquote {
  border-left-color: var(--brand-accent);
}

[data-theme="light"] .menu__link.menu__link--active {
  background: color-mix(in srgb, var(--brand-primary) 18%, white);
  border-left-color: var(--brand-primary);
}
```

For component files, make the same hue swap, not a structural redesign:

```tsx
// src/components/GlassCard/index.tsx
"border border-[color:color-mix(in_srgb,var(--brand-primary)_20%,transparent)] bg-white/70 ..."
```

```css
/* src/components/CategoryCard/styles.module.css */
background: color-mix(in srgb, var(--brand-primary) 10%, transparent);
border-color: color-mix(in srgb, var(--brand-primary) 20%, transparent);
```

```jsx
// src/theme/Navbar/Logo/index.js
isDarkTheme
  ? "bg-gradient-to-br from-[var(--brand-primary)]/20 to-[var(--brand-accent)]/20 ..."
  : "bg-gradient-to-br from-[var(--brand-primary)]/10 to-[var(--brand-accent)]/10 ..."
```

```tsx
// src/components/CategoryGrid/index.tsx
className="font-display text-4xl md:text-5xl font-bold ..."
```

- [ ] **Step 5: Prove the purple migration is complete in the active UI**

Run:

```bash
npm run lint && npm run typecheck
```

Then check for leftovers:

```bash
rg "purple-|168,\s*85,\s*247|147,\s*51,\s*234" src/css src/components src/theme/Navbar
```

Expected: no matches in the touched surface area except intentionally out-of-scope personal placeholder components.

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json src/css/custom.css src/components/GlassCard/index.tsx src/components/CategoryCard/styles.module.css src/components/CategoryGrid/index.tsx src/components/CategoryGrid/styles.module.css src/theme/Navbar/Logo/index.js
git commit -m "feat: apply midnight coral theme"
```

---

### Task 4: Refresh the homepage hero and finish verification

**Files:**
- Modify: `src/pages/index.tsx`
- Modify: `src/pages/index.module.css`

**Interfaces:**
- Consumes: `HomeIntro`, `RecentDocs`, `GlassCard`, and the brand tokens from earlier tasks.
- Produces: homepage hero with tokenized gradients, new blob drift animation, and reduced-motion-safe behavior.

- [ ] **Step 1: Recolor the hero text and blobs in `index.tsx`**

Use inline arbitrary values so the blobs and title are driven by the new tokens instead of Tailwind’s purple/blue presets:

```tsx
<div className="absolute left-0 top-0 h-128 w-lg rounded-full bg-[var(--brand-primary)]/25 mix-blend-multiply blur-3xl animate-pulse [animation:var(--blob-animation),var(--aurora-animation)]" />
<div className="absolute right-0 top-20 h-96 w-96 rounded-full bg-[var(--brand-accent)]/20 mix-blend-multiply blur-3xl animate-pulse [animation-delay:3s,0s]" />
<div className="absolute bottom-0 left-1/2 h-96 w-96 rounded-full bg-[color:color-mix(in_srgb,var(--brand-primary)_55%,var(--brand-accent))]/20 mix-blend-multiply blur-3xl animate-pulse [animation-delay:2s,6s]" />
```

And update the main hero heading classes to include the display font and new gradient:

```tsx
className="font-display text-5xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent [background-image:linear-gradient(to_right,var(--brand-primary-light),var(--brand-accent-light),var(--brand-primary))]"
```

- [ ] **Step 2: Update the page CSS for the new gradient and drift motion**

In `src/pages/index.module.css`, replace the hardcoded hero gradients with token-based ones:

```css
.heroGradient {
  background: linear-gradient(
    to bottom right,
    var(--brand-bg-start),
    color-mix(in srgb, var(--brand-accent) 18%, var(--brand-bg-start)),
    var(--brand-bg-end)
  );
}
```

Add the drift animation and reduced-motion guard:

```css
@keyframes auroraDrift {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  33% { transform: translate3d(2rem, -1rem, 0) scale(1.05); }
  66% { transform: translate3d(-1.5rem, 1.5rem, 0) scale(0.98); }
  100% { transform: translate3d(0, 0, 0) scale(1); }
}

.blobDrift {
  animation: auroraDrift 20s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .blobDrift {
    animation: none;
  }
}
```

Apply `.blobDrift` to the three orb divs in `index.tsx`.

- [ ] **Step 3: Run the full verification pass**

Run:

```bash
npm run typecheck
npm run lint
npm run build
```

Expected:
- typecheck passes
- lint passes on the modified files
- build passes with no broken links and no plugin errors

- [ ] **Step 4: Do the manual browser check**

Run `npm run start`, open the local site, and confirm:
- homepage in light mode uses the new palette and Space Grotesk on hero/category/recent-doc headings
- homepage in dark mode keeps good contrast
- personal intro strip appears between hero and categories
- recent-docs cards render real updated docs, not an empty placeholder
- a doc page does **not** show a visible “Last updated” line
- the hero blobs drift in normal motion mode and stop drifting with reduced motion

- [ ] **Step 5: Commit**

```bash
git add src/pages/index.tsx src/pages/index.module.css
git commit -m "feat: polish midnight coral homepage"
```

---

## Self-Review Notes

- **Spec coverage:** Task 1 covers the recent-docs plugin, docs metadata source, and hidden per-doc update UI. Task 2 covers the intro strip and homepage feed. Task 3 covers the token system, font import, and site-wide hue migration. Task 4 covers the hero recolor, drift animation, and final manual/build verification.
- **No placeholders:** every task names exact files, exact interfaces, concrete code, and literal commands.
- **Type consistency:** the only shared data contract is `RecentDocsPluginData`/`RecentDocSummary`, and the same field names (`title`, `description`, `permalink`, `lastUpdatedAt`) are used consistently across plugin and component tasks.
