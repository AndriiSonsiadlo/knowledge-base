# Navbar Three-Column Refactor Design

Date: 2026-07-30
Status: Approved for planning

## Summary

Refactor the Docusaurus navbar from a stretched two-bucket layout into a strict three-column desktop system with explicit visual grouping:

- **Left**: logo mark and site title
- **Center**: navigation categories
- **Right**: GitHub button, theme button, search

The goal is not a cosmetic cleanup. The goal is to replace the current layout contract so the navbar has clear hierarchy, centered navigation, consistent spacing, stable responsive behavior, and production-grade visual balance.

Desktop navigation remains available until roughly **1280px**. Below that width, the center navigation yields to the existing Docusaurus mobile/sidebar pattern so search and utility controls never have to compete with the category links.

## Problems to Solve

### Layout architecture

- The current navbar groups logo and navigation on the left, with utilities on the right, so the navigation area is never truly centered.
- Utility controls are pushed into the corner instead of reading as one grouped action rail.
- The bar feels horizontally stretched but vertically cramped.
- The layout budget is implicit, so spacing compensates for structural issues.

### Spacing system

- Some relationships are too tight while others are too loose.
- The categories begin too close to the brand.
- Search and utility controls do not share a unified rhythm.
- Margins, gaps, and transforms are currently doing too much of the layout work.

### Search and actions

- The search field does not feel like part of a coherent right-side system.
- Search width is not balanced against navigation width.
- GitHub and theme buttons attract too much attention for their role.
- The theme state is visually heavier than a utility control should be.

### Visual hierarchy

- Brand, navigation, search, and utility actions compete at nearly the same visual weight.
- The eye does not get a clear first, second, and third read.
- The current navbar feels tuned by local overrides rather than one system.

## Goals

- Replace the desktop navbar with a **strict three-column layout**.
- Keep the **center navigation visually centered** regardless of search width.
- Use a **single spacing scale** for brand, nav, actions, and search.
- Reduce the visual weight of GitHub and theme controls.
- Keep search visible, aligned, and present without letting it dominate.
- Preserve the existing mobile/sidebar behavior below the approved collapse width.
- Keep the glass surface, but remove extra decorative noise.
- Make the resulting navbar feel like a production-quality navigation system rather than a Docusaurus navbar with patches.

## Non-Goals

- Rework the site information architecture or rename navbar categories.
- Redesign the mobile sidebar beyond what is required for a clean handoff from desktop.
- Add new decorative effects such as extra gradients, glows, or more aggressive shadows.
- Introduce unrelated refactors outside the navbar surface.

## Approved Product Decisions

- Desktop full navigation remains visible until **about 1280px**.
- The approved technical direction is to **swizzle `Navbar/Content`** and rebuild the desktop structure around real left / center / right groups.
- The desktop active nav state uses **one subtle underline indicator**. It does not combine underline and accent pill.
- The right rail order is: **GitHub → Theme → Search**.
- Search keeps a visible inline desktop field and collapses appropriately on compact widths.
- The visible keyboard shortcut hint stays hidden.

## Current Structural Constraint

The stock Docusaurus navbar content component renders a left container and a right container. In that model, the logo and nav links live together on the left while the controls and search live on the right. That is the root reason the navigation cannot be treated as a truly centered system.

This refactor replaces that default desktop contract with a custom content composition while preserving Docusaurus item rendering and mobile sidebar behavior.

## Chosen Approach

### Recommended and approved

Create a custom `src/theme/Navbar/Content/index.js` that explicitly composes three desktop rails:

1. **Brand rail**
2. **Navigation rail**
3. **Action rail**

This is the minimum structural change that satisfies the design goal. It avoids the compromises of a CSS-only workaround while staying less invasive than building a fully bespoke navbar framework.

## Layout Architecture

### Desktop shell

The desktop navbar becomes:

- a full-width sticky glass surface
- an inner centered content container
- a three-column desktop layout with explicit width responsibilities

### Column model

#### Left rail: brand

Contains:

- logo mark
- site title

Behavior:

- fixed-width rail
- anchored to the left edge of the inner container
- visually stable so the brand does not shift when the right rail changes width

Target width:

- approximately **220px to 240px**

#### Center rail: navigation

Contains:

- desktop navigation categories only

Behavior:

- flexible center rail
- centered within its own column, not merely pushed by leftover space
- isolated from the right rail so search width changes do not visibly drag navigation off-center

#### Right rail: actions

Contains:

- GitHub button
- theme button
- search field

Behavior:

- auto-width rail
- grouped as one action cluster
- aligned to the right edge of the inner container
- compact, consistent, and visually subordinate to the brand and nav

## Desktop Spacing System

The navbar uses one explicit scale instead of ad hoc local gaps.

### Container

- height: **68px**
- content vertically centered
- equal top and bottom inset
- no transparent dead space above or below the glass surface

### Brand rail

- logo box: **36px × 36px** visual footprint
- logo ↔ title gap: **12px**
- brand ↔ navigation separation: **48px** minimum at full desktop layout

### Navigation rail

- category item gap: **32px** target
- acceptable range: **28px to 36px** if implementation needs a minor responsive adjustment
- nav labels use a quieter weight than the brand title

### Action rail

- GitHub ↔ theme button gap: **12px**
- utility buttons ↔ search gap: **16px**
- icon buttons use identical outer dimensions
- search height aligns proportionally with those controls so the right rail reads as one system

## Visual Hierarchy

### Read order

1. **Brand**
2. **Navigation**
3. **Search and utility actions**

### Brand styling

- title weight steps down slightly from the current bold treatment
- brand remains the left anchor without becoming oversized
- logo mark stays crisp and recognizable, but not oversized relative to the bar height

### Navigation styling

- link weight is reduced slightly for better rhythm and readability
- inactive items stay quiet
- hover should be subtle and non-dominant
- active state uses a soft animated underline only

### Action styling

- GitHub and theme controls share the same size, border weight, radius, and hover behavior
- utility controls read as secondary tools, not focal buttons
- focus treatment remains accessible but lighter and less exaggerated than the current heavy treatment

## Search Behavior

### Desktop search

The desktop search field belongs to the right rail and should feel like part of the action cluster, not a separate floating subsystem.

Requirements:

- vertically aligned with GitHub and theme controls
- translucent theme-aware fill
- visually quieter than the center navigation
- visible keyboard shortcut hint removed
- width adapts without dominating the navbar

Target widths:

- large desktop: **240px**
- medium desktop: **200px**
- tight desktop before collapse: **160px to 180px**

### Compact behavior

Below the desktop-collapse threshold, the navbar should stop trying to preserve the center navigation. The desktop categories yield to the mobile/sidebar model first.

Search then follows the existing compact pattern already present in the codebase:

- inline desktop field when supported
- compact trigger on narrow widths
- modal search path for compact/mobile interaction

The compact trigger must use the same button system as the GitHub and theme controls.

## Responsive Behavior

### At or above ~1280px

- logo mark and site title visible
- desktop category links visible in the center rail
- GitHub, theme, and inline search visible in the right rail
- center navigation remains visually centered even when search width changes

### Below ~1280px

- desktop category links leave the top row and rely on the mobile/sidebar pattern
- brand remains anchored
- right-side controls stay grouped
- the navbar no longer tries to preserve a cramped desktop category row

### Narrower compact widths

- the compact search trigger remains available
- icon visibility may reduce in a predictable order if necessary
- the bar must never depend on scattered one-off spacing hacks to survive narrow widths

## Component Boundaries

### `src/theme/Navbar/Content/index.js`

New responsibility:

- explicit three-rail desktop composition
- continued use of Docusaurus navbar items
- clean split between desktop category content and right-side utilities
- preservation of the mobile sidebar toggle handoff

### `src/theme/Navbar/Layout/index.js` and `styles.module.css`

Responsibility:

- sticky shell
- glass surface behavior
- safe placement of blur/backdrop effects
- outer navbar height and vertical centering

### `src/theme/Navbar/Logo/index.js`

Responsibility:

- brand mark and title composition
- correct visual scale for the new left rail
- removal of unnecessary visual weight or oversized treatment

### `src/theme/Navbar/Search/index.js`

Responsibility:

- desktop search placement contract
- relationship between Docusaurus search bar and the custom right rail

### `src/components/navbar/ResponsiveSearch/*`

Responsibility:

- compact trigger behavior
- modal search behavior on compact/mobile widths
- shared alignment contract between inline and compact search states

### `src/css/custom.css`

Responsibility after refactor:

- shared navbar tokens and common rules
- not the primary source of architecture

## Accessibility and Interaction Rules

- Preserve keyboard access for all controls.
- Preserve and respect the existing search modal focus behavior.
- Maintain usable focus indication instead of removing it.
- Keep desktop targets at least comfortably clickable, with utility controls centered exactly.
- Do not rely on hover-only state changes to communicate function.

## Visual Constraints

The navbar should feel closer to the craft level of Linear, Vercel, Stripe, Raycast, or Apple in terms of:

- proportion
- spacing rhythm
- alignment
- visual quietness
- distribution of weight across the row

It should **not** add more decoration than the current system. The craft target is achieved through structure and restraint, not extra effects.

## Likely File Scope

- `src/theme/Navbar/Content/index.js` (new swizzle)
- `src/theme/Navbar/Layout/index.js`
- `src/theme/Navbar/Layout/styles.module.css`
- `src/theme/Navbar/Logo/index.js`
- `src/theme/Navbar/Search/index.js`
- `src/components/navbar/ResponsiveSearch/index.tsx`
- `src/components/navbar/ResponsiveSearch/styles.module.css`
- `src/css/custom.css`

## Verification Plan

Project verification after implementation:

1. `npm run typecheck`
2. `npm run lint`
3. `npm run build`

Manual verification after implementation:

- wide desktop
- around 1440px
- around 1280px
- around 1024px
- tablet widths
- compact mobile widths

Checks:

- navigation is visually centered on desktop
- brand feels anchored and not crowded by categories
- right-side controls read as one grouped system
- search does not dominate or disappear
- GitHub and theme buttons have identical dimensions
- underline active state is subtle and readable
- no overlap or crowding appears before the collapse threshold
- mobile/sidebar behavior still works after the desktop nav yields
- light and dark themes preserve alignment and visual balance

## Recommendation

Implement the navbar refactor as a structural rebuild of the desktop composition, not as another round of local spacing or control styling patches. The current issues come from the layout contract itself. Swizzling `Navbar/Content` to establish a real brand rail, navigation rail, and action rail solves the root problem and gives the rest of the spacing and styling decisions a stable foundation.