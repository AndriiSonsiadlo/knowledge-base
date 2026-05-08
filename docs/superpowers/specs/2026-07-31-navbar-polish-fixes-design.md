# Navbar Polish Fixes Design

Date: 2026-07-31
Status: Approved for planning

## Summary

This design is a focused follow-up to the recent responsive navbar work. The goal is not to redesign the navbar, but to clean up the remaining visual and interaction regressions in the current swizzled implementation: the navbar surface does not read as full-width, the blur is applied in a way that still feels transparent instead of deliberate, the topbar action spacing is too tight, the mobile sidebar header actions do not align cleanly, and the search modal does not fully reset when a result is selected.

The approved direction is a small structural refactor that preserves the current component map while normalizing action-rail layout, making the blurred navbar surface span the viewport, keeping GitHub/search/theme visible in the top bar at all widths, and tightening the modal lifecycle so search closes cleanly on navigation.

## Problems to Solve

- The navbar looks visually inset, with side margins, instead of reading as a full-width site chrome.
- The navbar surface feels too transparent; the intended blurred/glass treatment is not strong enough.
- Search and theme controls sit too close together in the top bar.
- The logo block and action buttons feel cramped.
- In the mobile sidebar header, the GitHub and theme buttons are not vertically aligned and the theme button sits low.
- The search modal stays open when a user clicks a search result, even though navigation succeeds.
- The search field inside the modal is shifted too far right and can appear slightly off-center or outside the visual bounds of the modal.

## Goals

- Make the navbar background/blur read as a full-width, intentional surface.
- Keep the inner navbar content aligned to the page container instead of spreading content edge-to-edge.
- Preserve the existing icon-triggered search modal pattern at every breakpoint.
- Keep GitHub, search, and theme visible together in the top bar at all widths.
- Prioritize utility controls over the full "Knowledge Base" text when space gets tight.
- Normalize action sizing, spacing, and vertical centering between the desktop navbar and the mobile sidebar header.
- Ensure the search modal closes immediately when a result is activated by mouse or keyboard.
- Keep keyboard and focus behavior intact for the modal.

## Non-Goals

- Replace the current swizzled navbar/search/sidebar architecture.
- Rework navbar content, doc sidebars, or Docusaurus navigation sources.
- Introduce a desktop inline search field.
- Change the site’s overall visual language beyond the navbar-related polish needed for this pass.

## Approved Product Decisions

- Use a **small refactor**, not a CSS-only patch and not a broader navbar rewrite.
- The navbar should be **full-width visually**, but its inner content should stay container-aligned.
- Search stays as an **icon button that opens a modal** on every breakpoint.
- GitHub should remain visible in the **top bar at all widths**, alongside search and theme.
- If space becomes constrained, the **brand text yields before utility controls**.

## Existing Architecture to Preserve

The current implementation already has the right high-level seams, so this pass should preserve them:

- `src/theme/Navbar/Layout/*` owns the sticky shell and backdrop-safe wrapper.
- `src/theme/Navbar/Search/*` delegates to the responsive search wrapper.
- `src/components/navbar/ResponsiveSearch/*` owns the compact search trigger and modal lifecycle.
- `src/theme/Navbar/MobileSidebar/Header/*` manually assembles logo, GitHub, theme toggle, and close button inside the sidebar header.

The design should improve boundaries inside this structure rather than replacing it.

## Structural Design

### 1. Navbar shell

The navbar should continue to use the current two-layer idea:

- an outer sticky `<nav>` shell that spans the viewport;
- an inner chrome layer that provides the visual surface.

The change is that the chrome must visually read as full-width instead of as a centered translucent strip. The full-width visual treatment should stay on a dedicated chrome layer rather than move onto `<nav>` itself, so the existing containing-block safety is preserved. Inside that full-width chrome, the content row remains aligned to the normal page width.

### 2. Content row

The inner navbar row remains container-aligned. This preserves alignment with page content and prevents the top navigation from feeling detached from the rest of the site.

### 3. Action rail

Desktop navbar actions and mobile sidebar header actions should follow the same conceptual model:

- shared control size;
- shared vertical centering rules;
- explicit gap values;
- no one-off margin utilities used as the primary layout mechanism.

This does not require extracting a new shared React component unless that proves clearly simpler during implementation; the design requirement is consistent layout behavior, not abstraction for its own sake.

## Interaction and Responsive Behavior

### Top bar behavior

- GitHub, search, and theme remain visible in the top bar at all widths.
- Increase the gap between search and theme so they stop reading as a fused control.
- Add slightly more separation between the brand block and the action rail.
- When space tightens, reduce brand-text presence before sacrificing the utility controls.

### Mobile sidebar header behavior

- Keep the current header composition of logo + GitHub + theme + close.
- Align GitHub and theme to the same vertical center.
- Ensure the theme toggle is centered within the same control box height as GitHub.
- Add explicit spacing between the logo area and the action buttons so the header no longer feels crowded.

### Search modal behavior

- Keep the existing open/close model, focus trapping, Escape handling, and focus return to the trigger.
- Fix modal-body layout so the search field is centered within the modal panel and does not drift right.
- When a search result is activated, clear modal-open state as part of the selection flow so the overlay is gone on the destination page.
- Mouse selection and keyboard selection should both follow the same close-on-navigation behavior.

## Error Handling and Safety Boundaries

- This pass must not change where navigation items come from in `docusaurus.config.js`.
- Search-close behavior should be additive to the current search plugin behavior, not a replacement for routing.
- If a navigation path bypasses the explicit close hook, navigation must still succeed normally.
- Theme switching must remain directly reachable from the top bar and must not regress into a sidebar-only action.
- The sticky shell must continue to avoid the known containing-block issue caused by putting `backdrop-filter` on the wrong layer.

## Likely File Scope

- `src/theme/Navbar/Layout/index.js`
- `src/theme/Navbar/Layout/styles.module.css`
- `src/css/custom.css`
- `src/components/navbar/ResponsiveSearch/index.tsx`
- `src/components/navbar/ResponsiveSearch/styles.module.css`
- `src/theme/Navbar/MobileSidebar/Header/index.js`

## Verification Plan

Because this repo has no automated test suite, verification for this pass should be manual plus project gates.

### Manual QA

Check all of the following in both light and dark theme:

- wide desktop;
- tablet / collapsed-nav widths;
- narrow mobile top bar;
- mobile sidebar open state.

Specific checks:

- navbar background/blur reads full-width;
- inner content remains page-aligned;
- search and theme have visible separation;
- logo/action spacing feels balanced;
- GitHub and theme align vertically in the sidebar header;
- theme remains visible in the top bar;
- GitHub remains visible in the top bar;
- search modal input is centered and fully inside the panel;
- clicking a search result closes the modal;
- keyboard activation of a search result also closes the modal;
- Escape, backdrop close, and focus return still work.

### Project checks

- `npm run typecheck`
- `npm run lint`
- `npm run build`

## Delivery Constraints

- Keep implementation scoped to the listed navbar/search/sidebar polish issues.
- Prefer the smallest structural change that makes the behavior reliable.
- Make short, concise commits during implementation.
- Do not add a co-author line to those commits.

## Recommendation

Implement this as a targeted polish pass on top of the recent responsive navbar refactor. The main issue is no longer overall responsive architecture; it is inconsistency between the full-width chrome, the action-rail layout, and the modal lifecycle. A small structural refactor is the right level of change: big enough to remove the current alignment/margin fragility, but narrow enough to avoid another full navbar rewrite.
