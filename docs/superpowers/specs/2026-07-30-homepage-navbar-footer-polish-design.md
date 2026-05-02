# Home page / navbar / footer visual polish

## Background

Follow-up refinement pass on top of the Midnight Coral rebrand
(`2026-07-30-midnight-coral-redesign-design.md`). Five concrete issues were
identified in the current implementation, plus an open-ended "make it more
beautiful" ask that was scoped down through brainstorming:

1. The "Categories" section title (`src/components/CategoryGrid`) renders as
   a flat near-black/near-white color while the hero title ("My Knowledge
   Base") uses a brand gradient text-fill. They should match.
2. The navbar's GitHub icon (`.header-github-link` in `src/css/custom.css`)
   and the dark-mode toggle button (`.navbar [class*='toggleButton']`)
   reference different CSS variables for color (`--ifm-navbar-link-color`
   vs `--brand-primary-dark`), so they render in visibly different shades.
   The toggle button also has no explicit flex-centering rule (it currently
   relies on Infima defaults), while the GitHub icon does, so their icon
   glyphs aren't guaranteed to align identically.
3. `CategoryCard` already has hover lift/shadow/icon-rotate; it's missing a
   more distinctive per-category effect.
4. The footer background (`.footer`, `.footer--dark` in `custom.css`) is a
   pale/flat gradient in light mode and a near-solid dark tone in dark mode
   — doesn't match the richer brand gradient used elsewhere.
5. General "add something beautiful" — narrowed via brainstorming to: home
   page stat counters, scroll-reveal animations, docs page polish, and a
   back-to-top button + cursor glow.

## Scope

- `src/components/CategoryGrid/styles.module.css`: gradient text for
  `.sectionTitle`.
- `src/css/custom.css`: unify GitHub icon / theme-toggle icon color and
  centering; richer footer gradient (light + dark).
- `src/components/CategoryCard/styles.module.css`: add glow-border-pulse
  hover effect, per category color.
- New reusable scroll-reveal wrapper + stat counter component, used on the
  homepage.
- Docs page polish: admonitions, code block chrome, reading time + scroll
  progress bar, sticky TOC active-indicator.
- New `BackToTop` button and cursor-glow effect (hero + categories section).
- Out of scope: color token system, fonts, recent-docs plugin, personal
  intro strip (already covered by the Midnight Coral spec). No new
  animation/UI library dependency — everything is built with plain CSS
  animations/transitions and small React hooks (`IntersectionObserver`,
  `mousemove`), consistent with the rest of the codebase (no framer-motion,
  no gsap currently in `package.json`).

## Design

### 1. Categories title gradient

`CategoryGrid/styles.module.css` `.sectionTitle` currently sets a solid
`color` per theme. Replace with the same gradient-text technique already
used by `.heroTitle` in `src/pages/index.module.css`:

```css
.sectionTitle {
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

The `text-shadow` rules (tuned for solid text) are dropped since they don't
apply usefully to clipped gradient text. The `::after` gradient underline
pseudo-element and its light/dark variants are unchanged.

### 2. Navbar icon color + centering unification

`.header-github-link`'s color rules are rewritten to reference the same
variables as `.navbar [class*='toggleButton']`, instead of
`--ifm-navbar-link-color`:

- Base color: `var(--brand-primary-dark)` (light theme default already
  applies; dark theme override sets `var(--brand-primary-lightest)`, same
  as the toggle button already does).
- Hover color: `var(--brand-primary-darkest)` in light mode (matching the
  toggle's hover), `var(--brand-primary-lightest)` in dark mode (already
  the case for both).

`.navbar [class*='toggleButton']` gains explicit
`display: flex; align-items: center; justify-content: center;` so both
controls center their glyph identically (the GitHub icon already has this
via `inline-flex`). No layout/size changes — both stay `2.65rem` circles.

### 3. Category card glow border pulse

Add a hover-only animated glow using each card's own accent RGB variable
(`--brand-primary-rgb` / `--brand-accent-rgb`, same pairing already used by
each `.card-{color}` variant's background gradient). Implemented as an
animated `box-shadow` on `.categoryCard:hover`, e.g.:

```css
@keyframes glowPulse {
  0%, 100% { box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2), 0 0 0 0 rgb(var(--glow-rgb) / 0.35); }
  50% { box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2), 0 0 26px 4px rgb(var(--glow-rgb) / 0.45); }
}

.categoryCard:hover {
  animation: glowPulse 1.8s ease-in-out infinite;
}
```

Each `.card-{color}` variant sets `--glow-rgb` to its own primary/accent RGB
value (e.g. `.card-cyan { --glow-rgb: var(--brand-accent-rgb); }`). Under
`prefers-reduced-motion: reduce`, the animation is disabled and a static
mid-intensity glow shadow is applied instead (consistent with the existing
reduced-motion handling for `.cardIcon`).

### 4. Footer rich gradient

Replace the current footer backgrounds with brand-gradient versions,
following the same `--brand-primary`/`--brand-accent` tokens used by the
hero:

- Light theme: multi-stop gradient from a light tint of `--brand-primary`
  through `--brand-accent-light` (richer than the current flat
  `#ebe3f2 → #cec3da`), keeping the existing inset highlight
  `box-shadow`.
- Dark theme: gradient from `--brand-bg-end` through a `color-mix` blend of
  `--brand-accent` (mirroring `.heroGradient`'s approach) instead of the
  current near-solid `#191524`.

`--footer-border-color` and the top border stay as-is; only the background
value changes.

### 5. Homepage stat counters

New `src/components/StatsSection` component, rendered on the homepage
between `HomeIntro` and `RecentDocs`. Computes counts from data already
available client-side via `useAllDocsData()` / sidebar structures (same
source `CategoryGrid` uses) — no invented numbers:

- Number of top-level categories (same set `CategoryGrid` renders).
- Total number of doc pages across all sidebars.
- Number of tags in use (via `useAllDocsData` tags data), if easily
  available; otherwise this stat is dropped rather than faked.

Rendered as 2–3 stat cards. A small `useCountUp(target, { start })` hook
animates each number from 0 to its target over ~1.2s once the section
scrolls into view (see #6), using `requestAnimationFrame`; respects
`prefers-reduced-motion` by rendering the final number immediately.

### 6. Scroll reveal wrapper

New `src/components/ScrollReveal` component: a thin wrapper using
`IntersectionObserver` (`useInView` hook, threshold ~0.15, `once: true`) that
toggles a CSS class adding a fade+slide-up transition
(`opacity 0→1`, `translateY(16px)→0`, ~500ms ease-out) when its children
enter the viewport. Applied around `HomeIntro`, the new `StatsSection`,
`RecentDocs`, and the `CategoryGrid` block in `src/pages/index.tsx`. No
animation when `prefers-reduced-motion: reduce` is set (content renders
visible immediately, same as the reduced-motion handling already used in
`CategoryCard`).

### 7. Docs page polish

- **Admonitions**: light styling pass in `custom.css` for
  `.theme-admonition-*` — refined left-border color per type using existing
  brand tokens where types map naturally (info/tip use brand-primary/accent
  tones), subtle icon-in-a-circle badge, soft background tint. No new
  admonition types.
- **Code blocks**: add a small language-label chip to the existing Prism
  code block header area (via swizzled or CSS-targeted
  `[class*='codeBlockTitle_']` / `pre` container) and a subtle top-border
  accent using brand tokens. Existing copy-button behavior (Docusaurus
  default) is untouched.
- **Reading time + scroll progress**: swizzle `src/theme/DocItem/Layout` (or
  the smallest wrappable child) to add: (a) a slim fixed progress bar at the
  top of the viewport that fills as the user scrolls through the doc body,
  and (b) a computed "~N min read" label near the doc title, based on word
  count of the rendered content.
- **TOC**: style the existing right-hand TOC (`src/theme` — check for an
  existing TOC swizzle first) so the active heading indicator uses a small
  gradient bar (same gradient family as the navbar link underline) instead
  of the current default Infima indicator.

### 8. Back-to-top button + cursor glow

- **BackToTop**: new small floating circular button (bottom-right, fixed),
  shown once the user has scrolled past ~600px, smooth-scrolls to top on
  click. Rendered once, site-wide, via a `Root` theme swizzle
  (`src/theme/Root`) if one doesn't already exist, otherwise via the
  existing `Root`/`Layout` override point. Styled consistent with the
  navbar's circular icon-button treatment (`2.65rem`, brand-purple border/
  background, hover lift).
- **Cursor glow**: a `CursorGlow` component that renders a fixed,
  pointer-events-none `radial-gradient` div tracking the mouse position
  (via a throttled `mousemove` listener) over the hero (`.heroGradient`)
  and categories (`CategoryGrid`) sections only. Disabled on touch devices
  (`(hover: hover) and (pointer: fine)` media check) and under
  `prefers-reduced-motion: reduce`.

## Testing

No test suite exists in this repo (per `AGENTS.md`/`CLAUDE.md`). Verification
is: `npm run build` (catches broken links/build errors), `npm run typecheck`,
`npm run lint`, and manual visual check via `npm run start` in both light and
dark themes, at desktop and mobile widths, plus a manual check with OS
"reduce motion" enabled to confirm animations are suppressed.
