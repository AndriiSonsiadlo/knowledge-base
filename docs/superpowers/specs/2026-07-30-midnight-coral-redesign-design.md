# Midnight Coral redesign

## Background

The site's current visual identity is a single violet/purple hue reused
everywhere (`--ifm-color-primary` chain, plus many hardcoded Tailwind
`purple-*` / `rgba(168,85,247,...)` values scattered across
`src/css/custom.css`, `CategoryCard`, the hero gradient text, sidebar, TOC,
pagination, and footer). It works but doesn't distinguish the site from any
other purple-branded dev-tool/doc site. The homepage is a static hero +
category grid with no returning-visitor hook and no personal identity beyond
the title text. Font is the default system stack throughout.

Prior session already fixed three unrelated, narrower issues (committed
separately, not part of this spec): footer height/density, navbar item
overlap below ~1400px, and long shell commands wrapping mid-line in code
blocks.

This spec covers a deliberate rebrand: a new "Midnight Coral" color identity,
one display font for headings, two new homepage sections, and a subtle
animated hero background — chosen collaboratively via mockup comparison
(palette options A–D, typography options A–D) during brainstorming.

## Scope

- Introduce a token-based color system (`--brand-primary`, `--brand-accent`,
  shades) in `src/css/custom.css` and migrate existing hardcoded purple
  references site-wide (navbar, sidebar, links, code blocks, tables,
  blockquotes, admonitions borders, TOC, pagination, footer accents,
  `CategoryCard` variants, hero gradient text, focus ring) to reference them.
  Both light and dark theme variants.
- Add `@fontsource/space-grotesk` for headings/hero text only; body text
  keeps the current system font stack.
- Add a new Docusaurus content plugin (`src/plugins/recent-docs-plugin.js`)
  that surfaces the 6 most recently updated docs on the homepage, using real
  git-history data (no manual curation, no invented dates).
- Enable `showLastUpdateTime: true` on the docs preset (required for the
  plugin's data source) but suppress the resulting "Last updated on ..."
  UI on individual doc pages via a `DocItem` override, since only the
  homepage feed should surface it.
- Add a personal intro strip component to the homepage (name, avatar,
  one-line description, GitHub link — content confirmed with the project
  owner, not invented).
- Recolor and enhance the existing animated hero background blobs (already
  present in `src/pages/index.tsx`) with the new palette and an added slow
  drift animation.
- Out of scope: the placeholder `about-me` page/`Personal/*` components
  (still Lorem Ipsum, not linked in nav) — untouched by this spec. No new
  UI framework/animation library is introduced.

## Design

### 1. Color tokens

Add to `src/css/custom.css`, alongside the existing `:root` / `[data-theme='dark']`
blocks:

```css
:root {
  --brand-primary: #7c5cff;      /* violet — interactive elements, links */
  --brand-primary-dark: #6a46f0;
  --brand-primary-light: #a992ff;
  --brand-accent: #ff6b6b;       /* coral — gradients, highlights, badges */
  --brand-accent-light: #ff8f8f;
  --brand-bg-start: #f8f6fb;     /* light-mode background gradient */
  --brand-bg-end: #fdeeee;
}

[data-theme='dark'] {
  --brand-primary: #7c5cff;
  --brand-primary-dark: #5b3ff0;
  --brand-primary-light: #a992ff;
  --brand-accent: #ff6b6b;
  --brand-accent-light: #ff8f8f;
  --brand-bg-start: #120c1e;     /* dark-mode background gradient */
  --brand-bg-end: #1d1330;
}
```

`src/pages/index.module.css`'s `.heroGradient` background
(`linear-gradient(to bottom right, ...)`, both the dark-mode and
`html[data-theme='light']` variants) is updated to use
`var(--brand-bg-start)` / `var(--brand-accent)` / `var(--brand-bg-end)` as
its three stops instead of the current hardcoded `#0f172a`/`#581c87` (dark)
and `#f8fafc`/`#f3e8ff` (light) values — this is the only consumer of the
`--brand-bg-start/-end` tokens.

`--ifm-color-primary` and its `-dark/-darker/-darkest/-light/-lighter/-lightest`
shades are recalculated from `--brand-primary` (same structure as today, new
hue). Every existing hardcoded `purple-*` / `rgba(168,85,247,...)` /
`rgba(147,51,234,...)` occurrence in `custom.css` and
`CategoryCard/styles.module.css` is replaced with `var(--brand-primary)` /
`var(--brand-accent)` (adjusting alpha per existing rule, not redesigning
each rule's opacity/blur values). This is a like-for-like hue swap, not a
rewrite of each component's structure.

### 2. Typography

Add `@fontsource/space-grotesk` (weights 500/700) as a dependency, imported
once in `src/css/custom.css` (`@import '@fontsource/space-grotesk/500.css';`
etc., consistent with how Tailwind/theme CSS is already imported there).
New CSS variable `--font-display: 'Space Grotesk', var(--ifm-font-family-base);`
applied to `.markdown h1/h2/h3`, the hero `<Heading>` in `index.tsx`, and
`CategoryGrid`'s "Categories" heading. Body text, nav links, sidebar, and
docs paragraph text are untouched (still the existing system stack) —
keeps the change low-risk and avoids body-text FOUT.

### 3. Recently Updated Docs (homepage)

**Plugin** (`src/plugins/recent-docs-plugin.js`, registered in
`docusaurus.config.js` `plugins` array next to the existing custom plugins):

```js
module.exports = function recentDocsPlugin(_context, options = {}) {
  return {
    name: "recent-docs-plugin",
    async allContentLoaded({ allContent, actions }) {
      const docsContent = allContent["docusaurus-plugin-content-docs"]?.default;
      if (!docsContent) return;
      const docs = docsContent.loadedVersions
        .flatMap((v) => v.docs)
        .filter((d) => !d.unlisted && !d.draft && d.lastUpdatedAt)
        .sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt)
        .slice(0, options.limit ?? 6)
        .map((d) => ({
          title: d.title,
          description: d.description,
          permalink: d.permalink,
          lastUpdatedAt: d.lastUpdatedAt,
        }));
      actions.setGlobalData({ docs });
    },
  };
};
```

This relies on the documented `allContentLoaded({allContent, actions})`
plugin lifecycle hook (confirmed present in
`@docusaurus/types` for the installed version) to read the docs plugin's
already-computed metadata — no hand-rolled permalink/slug reconstruction,
no extra git shelling out. Requires `showLastUpdateTime: true` in the
`classic` preset's `docs` options so `lastUpdatedAt` is populated from git
history instead of `null`.

**Homepage component** (`src/components/RecentDocs/index.tsx`): reads
`usePluginData('recent-docs-plugin')` and renders up to 6 cards (title,
description, relative "updated X ago" via `Intl.RelativeTimeFormat`, link).
Renders nothing if the list is empty (e.g., a fresh clone with no git
history) rather than showing an empty section.

**Suppressing on-page display:** `src/theme/DocItem/Layout/index.js` is
already swizzled; add a CSS rule (or wrap `<DocItemFooter>`) hiding the
`lastUpdated` element specifically on doc pages, so the git-derived data
still flows into the homepage plugin without adding visible UI to every doc
page.

### 4. Personal intro strip

New `src/components/HomeIntro/index.tsx`: avatar (`img/logo.png`, reusing
the existing site logo asset), "Andrii Sonsiadlo", one-liner "Software
engineer — documenting what I learn about computer science and building
things.", and a GitHub link using the existing `siteConfig.customFields.githubUrl`.
Plain Tailwind, no new dependency, placed between the hero and the category
grid in `src/pages/index.tsx`.

### 5. Hero motion

`src/pages/index.tsx`'s three existing blurred `animate-pulse` divs get:
recolored via the new `--brand-primary` / `--brand-accent` tokens (replacing
inline `bg-purple-500` / `bg-blue-500` / `bg-pink-500`), plus a new
`@keyframes auroraDrift` (slow `translate`/`scale` loop, ~20s, independent
per blob via `animation-delay`) layered on top of the existing opacity pulse
in `index.module.css`. `prefers-reduced-motion: reduce` disables the drift
(existing `animate-pulse` already respects Tailwind's reduced-motion
handling).

## Testing

- `npm run typecheck`
- `npm run lint` on touched files (repo has a pre-existing, unrelated
  tabs-vs-spaces Biome finding across most `src/` files — not introduced by
  this work, not fixed as part of it)
- `npm run build` — validates no broken links/broken plugin data, and
  confirms the recent-docs plugin doesn't throw when docs exist
- Manual check via browser preview: homepage in light + dark mode (palette,
  font, new sections, hero motion), a doc page (colors migrated correctly,
  no visible "Last updated" line), narrow-viewport navbar (still fine from
  the earlier fix)
- Confirm `recent-docs-plugin` output is non-empty against this repo's real
  git history (already has hundreds of commits touching `docs/`)

## Risks / open items

- `lastUpdatedAt` reflects git commit history, not manual `date` frontmatter
  — acceptable for this repo since docs are edited via normal commits.
- Enabling `showLastUpdateTime` recomputes git blame for every doc file at
  build time; this repo's build already completes quickly (confirmed
  ~fast build during prior session), so no meaningful build-time regression
  expected, but this should be watched if the docs tree grows much larger.
- Migrating every hardcoded purple reference to tokens touches many small
  CSS rules across `custom.css` and `CategoryCard/styles.module.css`; risk
  of missing a spot (leftover purple) is mitigated by grepping for
  `purple-`, `168, 85, 247`, and `147, 51, 234` after the change to confirm
  none remain outside intentionally-unrelated content (e.g. syntax-highlighted
  code samples in docs, which are not part of this rebrand).
