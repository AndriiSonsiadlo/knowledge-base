# Navbar Three-Rail Follow-up Design

Date: 2026-07-31
Status: Approved for planning

## Summary

This follow-up design corrects the remaining structural mismatch in the navbar. The current implementation still uses Docusaurus's default two-bucket navbar content layout, which groups the logo/title and all category links into the same left container. That structure makes true center alignment impossible and causes the right-side controls to fight for space with a left rail that is doing too much.

The approved direction is to swizzle `Navbar/Content` and render three explicit rails:

- left: hamburger + logo + site title
- center: category links
- right: GitHub + theme toggle + search

The mobile sidebar will stop duplicating GitHub and theme controls. Those actions will live only in the navbar.

## Problems to Solve

- The logo/title and category links are currently grouped into one left bucket instead of separate left and center rails.
- The category links cannot stay visually centered because their layout depends on the width of the brand rail.
- The gap between the theme toggle and search button is still too tight.
- GitHub and theme controls are duplicated between the navbar and the mobile sidebar header.
- The mobile sidebar currently carries controls that should remain navbar-owned.

## Goals

- Make the brand rail stay left-aligned at all widths.
- Make the category links live in a real center rail, not in the left bucket.
- Make GitHub, theme, and search live in a real right rail.
- Keep GitHub, theme, and search in the navbar rather than hiding theme or GitHub into the sidebar.
- Remove duplicate GitHub/theme controls from the mobile sidebar.
- Increase the visible gap between the theme toggle and search button.

## Non-Goals

- Redesign the navbar visual style from scratch.
- Change the site navigation model or the actual set of category links.
- Change the current search-modal interaction model.
- Rework the mobile sidebar beyond removing duplicated controls and preserving clean header layout.

## Root Cause

The current behavior is caused by Docusaurus's default `Navbar/Content` implementation, which renders:

- `NavbarMobileSidebarToggle + NavbarLogo + leftItems` into the left container
- `rightItems + NavbarColorModeToggle + NavbarSearch` into the right container

That means the current code is trying to achieve a three-rail layout with only two actual structural buckets. CSS can improve spacing, but it cannot reliably create a stable centered category rail while the brand and categories still share the same container.

## Approved Product Decisions

- Swizzle `src/theme/Navbar/Content/index.js` for explicit layout control.
- Use three explicit rails in the top navbar: left, center, right.
- Keep GitHub, theme, and search as navbar-only controls.
- Remove GitHub and theme from the mobile sidebar header.
- Preserve the existing compact search trigger + modal behavior.

## Structural Design

### Navbar content ownership

The navbar shell in `src/theme/Navbar/Layout/*` remains responsible for sticky behavior, chrome, blur, and container alignment.

A new swizzled `src/theme/Navbar/Content/index.js` becomes responsible for content zoning. It should render three explicit groups:

1. **Left rail**
   - hamburger toggle
   - logo
   - site title

2. **Center rail**
   - all category/doc navbar items currently configured as left-position items

3. **Right rail**
   - GitHub item
   - theme toggle
   - search trigger

### Sidebar ownership

`src/theme/Navbar/MobileSidebar/Header/index.js` should stop rendering GitHub and theme. The header should become a simpler brand-and-close row. The sidebar remains for navigation, not for duplicated utility controls.

## Interaction and Responsive Behavior

- The left rail stays pinned left.
- The center rail stays visually centered in the navbar.
- The right rail stays pinned right.
- The gap between theme and search should be increased relative to the current implementation.
- On widths where the category rail yields to the mobile/sidebar navigation pattern, the utility rail should still preserve GitHub, theme, and search together in the navbar instead of moving them into the sidebar.
- The sidebar should not contain a second copy of those utility controls.

## File Scope

- `src/theme/Navbar/Content/index.js` (new swizzle)
- `src/theme/Navbar/MobileSidebar/Header/index.js`
- `src/theme/Navbar/MobileSidebar/Header/styles.module.css`
- `src/css/custom.css`
- Possibly a CSS module paired with `Navbar/Content` if the three-rail structure is easier to keep local than global

## Verification Plan

Manual checks:

- desktop: logo/title on the left, category links centered, GitHub/theme/search on the right
- desktop: more space between theme and search
- tablet: rails remain visually separated and stable
- narrow/mobile navbar: GitHub/theme/search remain navbar-owned
- mobile sidebar open: no duplicated GitHub/theme controls in the sidebar header

Project checks:

- `npm run typecheck`
- changed-file Biome check
- `npm run build`

## Recommendation

Implement this follow-up as a structural navbar-content correction, not another CSS-only spacing pass. The actual problem is the two-bucket `Navbar/Content` DOM shape. Once that is replaced with explicit left, center, and right rails, the alignment and duplication issues can be fixed cleanly and predictably.
