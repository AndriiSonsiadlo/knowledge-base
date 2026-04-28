# GlassCard component extraction

## Background

`origin/dev/in_progress/home-page-tailwindcss` is a single-commit draft (2024-11-06,
diverged from master at `67f96c1`) adding `src/components/DocLayout.tsx` and
`src/components/GlassCard.tsx`. Neither is wired into any page. `DocLayout.tsx`
imports `./Navbar`, which does not exist at `src/components/` (only
`src/theme/Navbar`, Docusaurus's swizzled navbar) — the file does not compile
if anything ever imports it. The visual idea both files chase (animated
gradient-orb background + glassmorphism panel) already shipped on master,
independently, inside `src/pages/index.tsx` + `src/pages/index.module.css`
(`.glassCard`) — and master's version is more complete: it supports light
*and* dark theme via `html[data-theme="light"] .glassCard {...}`, while the
draft is dark-only.

Conclusion: the branch itself is dead. Nothing from it merges as-is. The
worthwhile follow-up is turning master's existing `.glassCard` CSS-module
class into a real reusable component, since it currently exists as inline
`clsx(styles.glassCard, ...)` duplicated across two spots in `index.tsx`
rather than as a component.

## Scope

- Add `src/components/GlassCard/index.tsx`.
- Migrate the two `.glassCard` usages in `src/pages/index.tsx` to `<GlassCard>`.
- Remove the now-dead `.glassCard` rules from `src/pages/index.module.css`.
- Do not touch `CategoryCard` (distinct color-variant gradient style, not a
  plain glass panel) or `about-me.js` (separate `background-grid` design
  system) — neither is a fit for this component.
- Do not merge `DocLayout.tsx` — redundant with the `Layout` + `heroGradient`
  wrapper every page already uses, and not needed by any current page.

## Design

**Component:** `src/components/GlassCard/index.tsx`, pure Tailwind classes,
no CSS module. This matches how `index.tsx` and `CategoryGrid/index.tsx`
already inline `dark:`-variant utility classes directly in JSX, and is one
fewer file than adding a co-located CSS module. Project's Tailwind v4 config
wires `dark:` to Docusaurus's theme attribute
(`@custom-variant dark (&:is([data-theme="dark"] *));` in `src/css/custom.css`),
so `dark:` classes track the site's actual light/dark toggle correctly.

```tsx
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean; // default false — current usages are static panels
}
```

Background/border/blur/shadow values are carried over unchanged from the
current `.glassCard` CSS (`rgba(0,0,0,0.4)` dark / `rgba(255,255,255,0.7)`
light, `backdrop-blur`, `1px solid` border, `1.5rem` radius, matching shadow)
expressed as Tailwind utility + `dark:` pairs. `className` merges via the
project's existing `cn()` helper (`src/lib/utils.ts`) so callers can still
add layout classes (padding, width, text-align) same as today.

**index.tsx changes:** replace both
`<div className={clsx(styles.glassCard, ...)}>` /
`<div className={styles.glassCard}>` with `<GlassCard className="...">`,
passing through the same extra utility classes each call site already had.

**Cleanup:** delete the `.glassCard` and
`html[data-theme="light"] .glassCard` rules from `index.module.css` once
nothing references them.

## Testing

- `npm run typecheck`
- `npm run build` (also validates internal links — `onBrokenLinks: "throw"`)
- `npm run start`, visually confirm the two panels on the homepage are
  pixel-equivalent to current master in both light and dark theme (toggle via
  the navbar theme switch).

## Out of scope

No other homepage/knowledge-base "beautification" changes — `CategoryCard`
and `about-me.js` were reviewed and don't fit the GlassCard pattern; nothing
else from the dev branch is worth carrying forward.
