# Navbar Polish Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the swizzled Docusaurus navbar so it has a full-width blurred surface, cleaner desktop/sidebar action alignment, and a search modal that stays centered and closes correctly on result navigation.

**Architecture:** Keep the current navbar/search/sidebar component map, but make the full-width visual chrome explicit in `Navbar/Layout`, normalize action-rail spacing with one shared sizing model, and tighten the `ResponsiveSearch` modal lifecycle with capture-phase close handling for result activation. Use a small dedicated CSS module for the mobile sidebar header instead of relying on margin utility classes.

**Tech Stack:** Docusaurus 3.10, React 19, TypeScript/JSX, CSS modules, global CSS overrides in `src/css/custom.css`, local search via `@easyops-cn/docusaurus-search-local`

## Global Constraints

- Keep implementation scoped to the listed navbar/search/sidebar polish issues.
- Prefer the smallest structural change that makes the behavior reliable.
- Make the navbar background/blur read as a full-width, intentional surface.
- Keep the inner navbar content aligned to the page container instead of spreading content edge-to-edge.
- Preserve the existing icon-triggered search modal pattern at every breakpoint.
- Keep GitHub, search, and theme visible together in the top bar at all widths.
- Prioritize utility controls over the full "Knowledge Base" text when space gets tight.
- Normalize action sizing, spacing, and vertical centering between the desktop navbar and the mobile sidebar header.
- Ensure the search modal closes immediately when a result is activated by mouse or keyboard.
- Keep keyboard and focus behavior intact for the modal.
- Use Node `>=20.0`.
- There is no automated test suite; verification must use manual QA plus `npm run typecheck`, `npm run lint`, and `npm run build`.
- Make short, concise commits during implementation.
- Do not add a co-author line to those commits.

---

## Planned File Structure

- **Modify:** `src/theme/Navbar/Layout/index.js` — add a dedicated inner content wrapper so the chrome can span the viewport while navbar content stays container-aligned.
- **Modify:** `src/theme/Navbar/Layout/styles.module.css` — keep the blur/background on the chrome layer, add the new inner content wrapper, and strengthen the glass treatment.
- **Modify:** `src/css/custom.css` — tune shared navbar spacing tokens, topbar action gaps, brand/action separation, and top-level control alignment.
- **Create:** `src/theme/Navbar/MobileSidebar/Header/styles.module.css` — own the sidebar-header layout instead of relying on `margin-right--*` utility classes.
- **Modify:** `src/theme/Navbar/MobileSidebar/Header/index.js` — group logo/actions explicitly, wire in the new CSS module, and normalize GitHub/theme/close alignment.
- **Modify:** `src/components/navbar/ResponsiveSearch/index.tsx` — keep the modal pattern, add result-activation close handling, and wrap modal search content in a centered shell.
- **Modify:** `src/components/navbar/ResponsiveSearch/styles.module.css` — center the search field inside the modal, ensure full-width input stays inside the panel, and preserve existing light/dark polish.

### Task 1: Stretch the navbar chrome while keeping content container-aligned

**Files:**
- Modify: `src/theme/Navbar/Layout/index.js`
- Modify: `src/theme/Navbar/Layout/styles.module.css`
- Modify: `src/css/custom.css`
- Test: manual QA in the dev server at wide desktop and tablet widths

**Interfaces:**
- Consumes: `NavbarLayout({ children })`
- Produces: `NavbarLayout({ children })` with `styles.navbarChrome` wrapping a new `styles.navbarContent`
- Produces: `styles.navbarContent` as the only container-alignment wrapper inside the blurred chrome
- Produces: navbar spacing tokens `--navbar-action-gap` and `--navbar-brand-gap` in `src/css/custom.css`

- [ ] **Step 1: Reproduce the current visual problem in the browser**

Run: `npm run start -- --host 0.0.0.0`
Expected: the sticky navbar appears as a centered translucent strip with visible side margins instead of a deliberate full-width chrome surface.

- [ ] **Step 2: Add an explicit inner content wrapper in `Navbar/Layout`**

Update `src/theme/Navbar/Layout/index.js` so the blurred chrome stays full-width and the navbar children sit inside a dedicated inner wrapper:

```jsx
<div className={styles.navbarChrome}>
  <div className={styles.navbarContent}>{children}</div>
</div>
```

Keep `NavbarBackdrop` and `NavbarMobileSidebar` outside that inner wrapper exactly as they are today.

- [ ] **Step 3: Add the new full-width chrome + container wrapper styles**

Update `src/theme/Navbar/Layout/styles.module.css` with the new inner wrapper and a stronger chrome treatment:

```css
.navbarChrome {
  position: relative;
  width: 100%;
  min-width: 0;
  min-height: 3.75rem;
  background: rgb(240 234 247 / 0.86);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.42),
    0 18px 36px rgb(15 23 42 / 0.08);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
}

.navbarContent {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: var(--ifm-container-width-xl);
  min-height: inherit;
  min-width: 0;
  margin: 0 auto;
  padding-inline: clamp(0.8rem, 2vw, 1rem);
  box-sizing: border-box;
}

:global([data-theme="dark"]) .navbarChrome {
  background: rgb(18 12 30 / 0.9);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.06),
    0 22px 44px rgb(0 0 0 / 0.28);
}
```

Do **not** move `backdrop-filter` onto `<nav>` itself.

- [ ] **Step 4: Move shared spacing intent into navbar-level tokens**

Update the navbar section in `src/css/custom.css` so the top bar has explicit action and brand spacing:

```css
.navbar {
  --navbar-control-size: 2.625rem;
  --navbar-control-icon-size: 18px;
  --navbar-action-gap: 0.68rem;
  --navbar-brand-gap: 0.7rem;
}

.navbar__items--right {
  gap: var(--navbar-action-gap);
}

.navbar__brand {
  gap: 0.55rem;
  margin-right: var(--navbar-brand-gap);
}
```

Keep the existing navbar control sizes unchanged in this task.

- [ ] **Step 5: Verify the shell visually before touching the sidebar or modal**

Check at wide desktop and around 996px width:
- the chrome spans the viewport edge-to-edge;
- the logo, nav links, search, GitHub, and theme controls still line up to the page content width;
- the stronger blur no longer reads as a mostly transparent strip.

- [ ] **Step 6: Run type checking after the layout wrapper change**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 7: Commit Task 1**

```bash
git add src/theme/Navbar/Layout/index.js src/theme/Navbar/Layout/styles.module.css src/css/custom.css
git commit -m "style: stretch navbar chrome"
```

### Task 2: Normalize desktop and sidebar action rails

**Files:**
- Create: `src/theme/Navbar/MobileSidebar/Header/styles.module.css`
- Modify: `src/theme/Navbar/MobileSidebar/Header/index.js`
- Modify: `src/css/custom.css`
- Test: manual QA in the dev server with the mobile sidebar open at 390px and 480px widths

**Interfaces:**
- Consumes: `.header-github-link`, `NavbarColorModeToggle`, `NavbarLogo`, `navbar-sidebar__close`
- Produces: `styles.sidebarBrand`, `styles.brandSlot`, `styles.actionRail`, `styles.utilityRail`, `styles.githubLink`, `styles.colorModeToggle`, `styles.closeButton`
- Produces: `NavbarMobileSidebarHeader()` that renders logo and controls as two explicit flex groups instead of four siblings with margin utility classes

- [ ] **Step 1: Reproduce the current alignment issue in the sidebar header**

Manual QA at 390px width:
- open the hamburger sidebar;
- confirm GitHub and theme are not sharing the same visual centerline;
- confirm the space between the logo and the action buttons feels cramped.

- [ ] **Step 2: Add a dedicated CSS module for sidebar-header layout**

Create `src/theme/Navbar/MobileSidebar/Header/styles.module.css` with explicit layout rules:

```css
.sidebarBrand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.9rem;
  width: 100%;
  min-width: 0;
}

.brandSlot {
  flex: 1 1 auto;
  min-width: 0;
}

.actionRail {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 0 0 auto;
}

.utilityRail {
  display: flex;
  align-items: center;
  gap: var(--navbar-action-gap);
}

.githubLink,
.colorModeToggle,
.closeButton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
```

Use the existing global `.header-github-link` and toggle button styling for appearance; this module only owns structure and alignment.

- [ ] **Step 3: Refactor the sidebar header markup into brand and action groups**

Update `src/theme/Navbar/MobileSidebar/Header/index.js` to remove `margin-right--sm` and `margin-right--md` and replace them with explicit wrappers:

```jsx
import styles from "./styles.module.css";

function GitHubLink({ className }) {
  // existing lookup logic unchanged
  return (
    <a
      href={githubItem.href}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx("header-github-link", styles.githubLink, className)}
      aria-label={label}
    >
      <span className="sr-only">{label}</span>
    </a>
  );
}

function CloseButton({ className }) {
  return (
    <button
      type="button"
      className={clsx("clean-btn", "navbar-sidebar__close", styles.closeButton, className)}
      onClick={() => mobileSidebar.toggle()}
      // existing aria-label unchanged
    >
      <IconClose color="var(--ifm-color-emphasis-600)" />
    </button>
  );
}

export default function NavbarMobileSidebarHeader() {
  return (
    <div className={clsx("navbar-sidebar__brand", styles.sidebarBrand)}>
      <div className={styles.brandSlot}>
        <NavbarLogo />
      </div>
      <div className={styles.actionRail}>
        <div className={styles.utilityRail}>
          <GitHubLink />
          <NavbarColorModeToggle className={styles.colorModeToggle} />
        </div>
        <CloseButton />
      </div>
    </div>
  );
}
```

Keep the GitHub lookup logic and close-button aria label text exactly as they are today.

- [ ] **Step 4: Tighten topbar spacing to match the new action-rail model**

Update `src/css/custom.css` so the desktop navbar and the sidebar header share the same spacing rhythm:

```css
.navbar__items--right > * {
  display: flex;
  align-items: center;
  min-height: var(--navbar-control-size);
}

.navbar__brand {
  margin-right: var(--navbar-brand-gap);
}

@media (max-width: 996px) {
  .navbar {
    --navbar-action-gap: 0.62rem;
    --navbar-brand-gap: 0.6rem;
  }
}

@media (max-width: 480px) {
  .navbar {
    --navbar-action-gap: 0.58rem;
    --navbar-brand-gap: 0.45rem;
  }
}
```

Remove the rule that hides `.header-github-link` at `max-width: 480px`; GitHub must remain visible in the top bar at every width.

- [ ] **Step 5: Verify the desktop and sidebar action rails manually**

Check these points:
- search and theme are no longer touching visually in the top bar;
- the gap between the logo block and the action rail feels intentional;
- GitHub and theme align to the same visual height in the sidebar header;
- GitHub remains visible in the top bar at 360px and 390px widths.

- [ ] **Step 6: Run lint after the JSX + CSS cleanup**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 7: Commit Task 2**

```bash
git add src/theme/Navbar/MobileSidebar/Header/index.js src/theme/Navbar/MobileSidebar/Header/styles.module.css src/css/custom.css
git commit -m "style: align navbar actions"
```

### Task 3: Center the modal search field and close the modal on result activation

**Files:**
- Modify: `src/components/navbar/ResponsiveSearch/index.tsx`
- Modify: `src/components/navbar/ResponsiveSearch/styles.module.css`
- Test: manual QA in the dev server with modal search open on desktop and mobile

**Interfaces:**
- Consumes: `ResponsiveSearch({ children, className }: ResponsiveSearchProps)`
- Produces: `closeModal(options?: { restoreFocus?: boolean })`
- Produces: `handleResultActivation(event: MouseEvent | React.MouseEvent)` that closes the modal when `event.target.closest("a[href]")` matches a search result link
- Produces: `styles.searchSurface` as a centered width-limited wrapper inside `.modalBody`

- [ ] **Step 1: Reproduce the current modal bugs**

Manual QA on any page with search results:
- open the search modal;
- confirm the search field sits too far right inside the modal panel;
- search for a page and click a result;
- confirm navigation happens but the overlay remains open during/after the transition.

- [ ] **Step 2: Make `closeModal` optionally skip focus restoration**

Update `src/components/navbar/ResponsiveSearch/index.tsx` so result activation can close the modal without pushing focus back to the trigger during navigation:

```tsx
type CloseModalOptions = {
  restoreFocus?: boolean;
};

const closeModal = useCallback(
  ({ restoreFocus = true }: CloseModalOptions = {}) => {
    setIsOpen(false);

    if (!restoreFocus || typeof window === "undefined") {
      return;
    }

    window.requestAnimationFrame(() => {
      triggerRef.current?.focus();
    });
  },
  [],
);
```

Keep all existing Escape and focus-trap behavior wired through this helper.

- [ ] **Step 3: Add capture-phase result-activation closing inside the modal body**

In `src/components/navbar/ResponsiveSearch/index.tsx`, add a result-activation handler and wrap `children` in a centered shell:

```tsx
const handleResultActivation = useCallback(
  (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement | null;
    if (!target?.closest("a[href]")) {
      return;
    }
    closeModal({ restoreFocus: false });
  },
  [closeModal],
);

<div
  className={styles.modalBody}
  onClickCapture={handleResultActivation}
>
  <div className={styles.searchSurface}>{children}</div>
</div>
```

A keyboard-activated search result link also emits a click event, so this handler covers both mouse and Enter-based selection.

- [ ] **Step 4: Center the modal search content with a dedicated inner shell**

Update `src/components/navbar/ResponsiveSearch/styles.module.css`:

```css
.modalHeader {
  align-items: center;
}

.modalBody {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 0.85rem;
  min-height: 0;
  padding: 0 1rem 1rem;
}

.searchSurface {
  width: min(100%, 36rem);
  min-width: 0;
  margin: 0 auto;
}

.searchSurface :global(.navbar__search),
.searchSurface :global([class^='searchBarContainer_']) {
  display: block;
  width: 100%;
  min-width: 0;
  max-width: none;
  margin: 0;
}

.searchSurface :global(.navbar__search-input) {
  width: 100%;
  padding: 0 3rem 0 2.75rem;
}
```

Keep the existing dropdown, loading ring, clear button, and dark-theme rules, but scope them through `.searchSurface` instead of relying on the full `.modalBody` width.

- [ ] **Step 5: Verify modal behavior manually on both desktop and mobile widths**

Check all of these:
- the input is centered and fully inside the modal panel;
- the dropdown stays aligned to that centered field;
- clicking a search result closes the modal before the destination page settles;
- keyboard selection of a result also closes the modal;
- Escape, backdrop click, and focus return to the trigger still work when the user closes the modal directly.

- [ ] **Step 6: Run the full project verification commands**

Run:
- `npm run typecheck`
- `npm run lint`
- `npm run build`

Expected: all PASS

- [ ] **Step 7: Commit Task 3**

```bash
git add src/components/navbar/ResponsiveSearch/index.tsx src/components/navbar/ResponsiveSearch/styles.module.css
git commit -m "fix: polish search modal"
```

## Self-Review Checklist

- **Spec coverage:**
  - full-width blurred navbar surface with container-aligned content: Task 1
  - stronger blur / less transparent chrome treatment: Task 1
  - more space between search and theme: Task 2
  - more space between logo block and action rail: Tasks 1 and 2
  - GitHub visible in top bar at all widths: Task 2
  - sidebar GitHub/theme alignment and centering: Task 2
  - modal input centered inside the panel: Task 3
  - modal closes on search-result activation: Task 3
  - keyboard/focus behavior preserved: Task 3
  - manual QA plus `typecheck`, `lint`, and `build`: Tasks 1 through 3
- **Placeholder scan:** no `TODO`, `TBD`, or undefined "fix later" steps remain.
- **Type consistency:** `ResponsiveSearchProps`, `closeModal(options?: { restoreFocus?: boolean })`, and the new sidebar-header style names are defined once and reused consistently.
