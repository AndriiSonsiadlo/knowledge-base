# Navbar Responsive Layout Design

Date: 2026-07-30
Status: Approved for planning

## Summary

Redesign the Docusaurus navbar so it uses a deliberate responsive flex layout instead of relying on the current default inner layout plus isolated search-input overrides. The new design keeps the full search field anchored to the far right on widths that can support it, protects the hamburger from overlap at every breakpoint, and degrades predictably down to 320px mobile width.

The approved direction is a three-zone flex shell with a responsive search wrapper. On the narrowest widths, the top bar keeps only the hamburger, logo mark, and a compact search trigger. Tapping the trigger opens search in a modal.

## Problems to Solve

- The current search bar can collide with the hamburger on small screens.
- The search container can consume too much width because only the input is constrained today.
- Navbar items do not have a single explicit flex budget across breakpoints.
- Important controls become cramped while empty space remains elsewhere in the bar.
- Alignment and spacing are inconsistent across brand, icons, and search.
- Breadcrumbs must remain correctly positioned below the sticky navbar.

## Goals

- Use a robust responsive Flexbox layout.
- Keep the hamburger fully visible, clickable, and visually separated from search at all widths.
- Keep the full search field on the far right whenever a full field is shown.
- Let search grow and shrink responsively using `flex-grow`, `flex-shrink`, `min-width: 0`, and width constraints such as `clamp()`, `min-width`, and `max-width`.
- Hide secondary search UI, especially the keyboard shortcut hint, before primary controls become cramped.
- Prevent overlap, clipping, and horizontal overflow from 320px mobile through desktop.
- Maintain consistent vertical alignment, spacing, glassmorphism styling, borders, blur, shadows, and motion polish.
- Preserve breadcrumb positioning below the navbar.

## Non-Goals

- Rework the site information architecture or navbar content model.
- Redesign the mobile sidebar itself beyond what is necessary for control placement.
- Change the established purple gradient and glassmorphism visual language.

## Approved Product Decisions

- On the narrowest widths, search becomes a compact trigger instead of staying as a full inline field.
- On widths where the full field is shown, search remains anchored to the far-right control group.
- When space gets tight, brand text yields before critical controls are compressed.
- On the narrowest widths, only the hamburger, logo mark, and compact search trigger must remain visible in the top bar.
- The compact search trigger opens search in a modal.

## Yield Order

When horizontal space tightens, the navbar should degrade in this exact order:

1. Desktop doc links leave the top row and rely on the sidebar pattern.
2. Brand text hides, leaving the logo mark.
3. Keyboard shortcut hint hides.
4. At the compact-search breakpoint, GitHub and theme toggle leave the top row.
5. The full search field is replaced by the compact search trigger.

At no point may the hamburger, logo mark, or active search entry point overlap or become partially hidden.

## Layout Architecture

### High-level structure

The navbar should behave as an explicit three-zone flex shell inside the existing sticky navbar container:

1. **Left cluster**: hamburger, brand, and desktop nav links.
2. **Flexible middle budget**: not a separate visible element, but the remaining width shared through flex rules.
3. **Right cluster**: GitHub, theme toggle, and search.

The important change is that space allocation moves from implicit Docusaurus defaults to explicit sizing rules.

### Flex rules

#### Left cluster

- `flex: 1 1 auto`
- `min-width: 0`
- Holds the desktop doc links on wide screens.
- Gives up space cleanly without forcing overflow.

#### Right cluster

- Right-aligned and anchored to the far edge.
- `min-width: 0`
- Width bounded with `clamp(...)` plus explicit `min-width` and `max-width`.
- Contains the search wrapper, not just the raw input, so the cluster can shrink as a unit.

#### Fixed-size controls

- Hamburger, GitHub icon, theme toggle, and compact search trigger use `flex-shrink: 0`.
- These controls must never collapse or become partially hidden.

## Breakpoint Behavior

### Wide desktop

- Brand logo and brand text visible.
- Top-row doc links visible.
- GitHub and theme toggle visible.
- Full search field visible on the far right.
- Keyboard shortcut hint visible if space comfortably allows.

### Mid-width / tablet

- Top-row doc links leave the navbar first and rely on the sidebar pattern.
- Brand text may hide, leaving the logo mark.
- GitHub and theme toggle remain visible until the compact-search breakpoint is reached.
- Full search field remains visible and right-aligned.
- Shortcut hint hides before the search field becomes cramped.

### Narrow mobile (roughly 320px–480px)

- Top bar keeps only:
  - hamburger
  - logo mark
  - compact search trigger
- GitHub and theme toggle no longer compete for top-row space.
- The compact trigger opens modal search.
- No top-row element may overlap another or force horizontal scrolling.

## Search Behavior

### Full-field mode

When the viewport can support an inline search field:

- Search remains on the far right.
- The **search wrapper** receives the responsive flex constraints.
- The input fills the wrapper instead of imposing its own rigid width.
- Secondary hint UI collapses before the main field becomes unusable.

### Compact mode

When the viewport becomes too narrow for a usable inline field:

- Replace the full field with a compact trigger button.
- The trigger uses the same visual language as the other circular utility controls.
- Activating the trigger opens a search modal.

### Modal behavior

- Open from the compact trigger on narrow widths.
- Focus moves directly into the modal search input.
- Closing the modal returns the user to the top navbar without layout shift.
- The modal path becomes the primary mobile search experience.

## Component Boundaries

### Navbar shell

Keep the current swizzled navbar layout wrapper as the shell that owns:

- sticky behavior
- backdrop-safe structure
- top-level spacing and alignment strategy

### Responsive search wrapper

Introduce a small navbar-focused search wrapper whose only responsibilities are:

- render the full inline search field on supported widths
- render the compact trigger on narrow widths
- manage modal open/close behavior

This prevents the implementation from pushing all responsive behavior into global CSS selectors.

### Existing navigation behavior

Continue to rely on existing Docusaurus navigation and sidebar behavior for:

- desktop nav links
- hamburger/sidebar navigation
- general navbar item rendering

The redesign should add targeted structure, not replace Docusaurus navigation wholesale.

## Alignment and Visual Rules

- All navbar items must share a common vertical alignment baseline.
- Spacing between right-side utility items must be explicit and consistent.
- Search, utility icons, and branding should feel balanced rather than packed to one side and loose on the other.
- The existing glassmorphism treatment stays intact:
  - translucent background
  - purple theme accents
  - borders
  - blur
  - shadows
  - hover motion
- Any new compact trigger or modal entry control must visually belong to the same design system as the GitHub and theme buttons.

## Breadcrumb Safety

- Preserve the current sticky navbar and breadcrumb offset relationship.
- Do not place `backdrop-filter`, `filter`, or transform behavior in a way that reintroduces containing-block issues for fixed descendants.
- The navbar may adapt in height if necessary, but breadcrumb positioning must remain stable and never slide under the bar.

## Robustness and Failure Handling

- The layout must degrade in a defined order instead of relying on accidental shrink behavior.
- If the enhanced mobile search path fails, there must still be a visible, reachable search entry point.
- Width constraints must live on the correct wrapper elements, not just the inner input.
- No breakpoint should depend on one fragile magic number alone; the design should combine flex rules, width bounds, and breakpoint-specific visibility rules.

## Likely File Scope

- `src/theme/Navbar/Layout/index.js`
- `src/theme/Navbar/Layout/styles.module.css`
- `src/css/custom.css`
- One targeted navbar/search override or wrapper component for compact-trigger and modal behavior

## Verification Plan

Manual QA targets:

- 320px
- 360px
- 390px
- 480px
- 640px
- 768px
- 996px
- 1200px
- wide desktop

Checks:

- Hamburger is always visible, clickable, and visually separated from search.
- Search never overlaps the hamburger or other controls.
- Full search stays aligned to the far right when shown.
- The shortcut hint hides before the field becomes cramped.
- No horizontal overflow, clipped content, or empty-space imbalance.
- Brand, icons, and search stay vertically aligned.
- Breadcrumbs remain below the navbar and are not covered.
- Light and dark themes preserve the intended polished visual style.

Project verification after implementation:

- `npm run typecheck`
- `npm run lint`
- `npm run build`

## Recommendation

Implement the navbar redesign as a structural responsive layout fix, not as another round of isolated input-width tweaks. The current overlap problem exists because the navbar does not yet have explicit space budgeting between left and right clusters. The approved three-zone flex shell plus responsive search wrapper addresses that root cause while staying consistent with the site’s existing design language.