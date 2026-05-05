# Navbar Responsive Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the navbar as a responsive flex layout that keeps search usable and right-aligned on supported widths, switches to a compact modal trigger on narrow mobile, and eliminates overlap with the hamburger across 320px-to-desktop viewports.

**Architecture:** Keep the existing swizzled navbar layout shell, but move responsive search behavior into a focused search wrapper and override the upstream `Navbar/Search` container that currently becomes `position: absolute` below 996px. Use explicit flex rules on the existing left and right navbar clusters so space is budgeted intentionally instead of being left to default Docusaurus layout behavior.

**Tech Stack:** Docusaurus 3.10, React 19, TypeScript/JSX, CSS modules, global CSS overrides, Biome, local search via `@easyops-cn/docusaurus-search-local`

## Global Constraints

- Use a robust responsive Flexbox layout.
- Keep the hamburger fully visible, clickable, and visually separated from search at all widths.
- Keep the full search field on the far right whenever a full field is shown.
- Let search grow and shrink responsively using `flex-grow`, `flex-shrink`, `min-width: 0`, and width constraints such as `clamp()`, `min-width`, and `max-width`.
- Hide secondary search UI, especially the keyboard shortcut hint, before primary controls become cramped.
- Prevent overlap, clipping, and horizontal overflow from 320px mobile through desktop.
- Maintain consistent vertical alignment, spacing, glassmorphism styling, borders, blur, shadows, and motion polish.
- Preserve breadcrumb positioning below the navbar.
- On the narrowest widths, search becomes a compact trigger instead of staying as a full inline field.
- On widths where the full field is shown, search remains anchored to the far-right control group.
- When space gets tight, brand text yields before critical controls are compressed.
- On the narrowest widths, only the hamburger, logo mark, and compact search trigger must remain visible in the top bar.
- The compact search trigger opens search in a modal.
- Use Node `>=20.0`.
- There is no automated test suite; verification must use manual QA plus `npm run typecheck`, `npm run lint`, and `npm run build`.

---

## Planned File Structure

- **Create:** `src/components/navbar/ResponsiveSearch/index.tsx` — controls full-search vs compact-trigger rendering, modal open/close state, focus handoff, and Escape/backdrop close behavior.
- **Create:** `src/components/navbar/ResponsiveSearch/styles.module.css` — styles the inline wrapper, compact trigger, modal backdrop/panel, and mobile search polish using the existing glassmorphism design language.
- **Create:** `src/theme/Navbar/Search/index.js` — wraps the active `SearchBar` in the responsive controller.
- **Create:** `src/theme/Navbar/Search/styles.module.css` — replaces the upstream absolute-positioned navbar search container with an in-flow flex container.
- **Modify:** `src/css/custom.css` — defines the three-zone flex layout, spacing, breakpoint yield order, and global navbar alignment rules.
- **Modify:** `src/theme/Navbar/Layout/styles.module.css` — adds any shell-level sizing or overflow rules needed to keep the backdrop-safe wrapper and sticky shell consistent.

### Task 1: Responsive search controller and search-container override

**Files:**
- Create: `src/components/navbar/ResponsiveSearch/index.tsx`
- Create: `src/components/navbar/ResponsiveSearch/styles.module.css`
- Create: `src/theme/Navbar/Search/index.js`
- Create: `src/theme/Navbar/Search/styles.module.css`
- Test: manual QA in the running dev server at 360px and 390px widths

**Interfaces:**
- Consumes: `children: ReactNode` from `@theme/SearchBar`
- Produces: `ResponsiveSearch({ children, className }: { children: ReactNode; className?: string })`
- Produces: mobile behavior driven by `const COMPACT_SEARCH_MEDIA = '(max-width: 480px)'`

- [ ] **Step 1: Reproduce the current failure in the browser**

Run: `npm run start -- --host 0.0.0.0`
Expected: at a narrow mobile width, the inline search area still competes with the hamburger or consumes more space than intended.

- [ ] **Step 2: Create the swizzled navbar search wrapper**

```js
import React from "react";
import clsx from "clsx";
import ResponsiveSearch from "@/components/navbar/ResponsiveSearch";
import styles from "./styles.module.css";

export default function NavbarSearch({ children, className }) {
  return (
    <ResponsiveSearch className={clsx(className, styles.navbarSearchContainer)}>
      {children}
    </ResponsiveSearch>
  );
}
```

- [ ] **Step 3: Replace the upstream absolute-positioned container with an in-flow flex container**

```css
.navbarSearchContainer:empty {
  display: none;
}

.navbarSearchContainer {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
  max-width: 100%;
}
```

Important: do **not** carry over the upstream `position: absolute` mobile rule from `@docusaurus/theme-classic/src/theme/Navbar/Search/styles.module.css`.

- [ ] **Step 4: Implement the responsive controller component**

```tsx
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Search, X } from "lucide-react";
import styles from "./styles.module.css";

const COMPACT_SEARCH_MEDIA = "(max-width: 480px)";

type ResponsiveSearchProps = {
  children: ReactNode;
  className?: string;
};

export default function ResponsiveSearch({ children, className }: ResponsiveSearchProps) {
  const [isCompact, setIsCompact] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const modalRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const media = window.matchMedia(COMPACT_SEARCH_MEDIA);
    const sync = () => setIsCompact(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!isCompact) setIsOpen(false);
  }, [isCompact]);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    const input = modalRef.current?.querySelector("input");
    if (input instanceof HTMLInputElement) input.focus();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isCompact) {
    return <div className={clsx(styles.inlineSearch, className)}>{children}</div>;
  }

  return (
    <div className={clsx(styles.compactSearch, className)}>
      <button
        type="button"
        className={styles.compactTrigger}
        aria-label="Open search"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(true)}>
        <Search size={18} />
      </button>
      {isOpen && (
        <div className={styles.modalBackdrop} onClick={() => setIsOpen(false)}>
          <div
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            className={styles.modalPanel}
            onClick={(event) => event.stopPropagation()}>
            <button
              type="button"
              className={styles.closeButton}
              aria-label="Close search"
              onClick={() => setIsOpen(false)}>
              <X size={18} />
            </button>
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Add component CSS for inline, trigger, and modal states**

```css
.inlineSearch {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
  justify-content: flex-end;
}

.compactSearch {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 0 0 auto;
}

.compactTrigger,
.closeButton {
  width: 2.65rem;
  height: 2.65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
}

.modalBackdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 5rem 1rem 1rem;
}

.modalPanel {
  width: min(40rem, 100%);
  min-width: 0;
}
```

Match the final colors, borders, blur, shadows, and hover states to the existing navbar utility controls in `src/css/custom.css`.

- [ ] **Step 6: Run type checking after adding the new component**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 7: Verify compact-search behavior manually**

Check at 360px and 390px widths:
- the top bar shows hamburger + logo mark + compact search trigger
- tapping the trigger opens the modal
- the modal focuses the search input
- Escape and backdrop close work

- [ ] **Step 8: Commit Task 1**

```bash
git add src/components/navbar/ResponsiveSearch/index.tsx src/components/navbar/ResponsiveSearch/styles.module.css src/theme/Navbar/Search/index.js src/theme/Navbar/Search/styles.module.css
git commit -m "feat: add responsive navbar search"
```

### Task 2: Three-zone flex layout and breakpoint yield order

**Files:**
- Modify: `src/css/custom.css`
- Modify: `src/theme/Navbar/Layout/styles.module.css`
- Test: manual QA at 640px, 768px, 996px, 1200px, and a wide desktop width

**Interfaces:**
- Consumes: `.navbar__inner`, `.navbar__items`, `.navbar__items--right`, `.navbar__brand`, `.navbar__toggle`, `.navbar__search-input`
- Produces: an in-flow three-zone flex shell where the right cluster stays far right and the left cluster can shrink without overflow

- [ ] **Step 1: Convert the navbar inner shell to an explicit flex layout**

Add or update rules in `src/css/custom.css`:

```css
.navbar__inner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.navbar__items {
  min-width: 0;
  align-items: center;
}

.navbar__items:first-child {
  flex: 1 1 auto;
}

.navbar__items--right {
  flex: 0 1 clamp(12rem, 28vw, 18rem);
  min-width: 0;
  margin-left: auto;
  justify-content: flex-end;
  gap: 0.5rem;
}
```

- [ ] **Step 2: Make the search wrapper and input shrink correctly inside the right cluster**

```css
.navbar__search,
[class^="searchBarContainer_"] {
  min-width: 0;
  flex: 1 1 auto;
}

.navbar__search-input {
  width: 100%;
  min-width: 7rem;
  max-width: 13.5rem;
}
```

Keep the existing custom search icon color override, but move width responsibility to the wrapper instead of the input alone.

- [ ] **Step 3: Encode the approved yield order as breakpoint rules**

```css
@media (max-width: 1400px) {
  .navbar__item {
    display: none;
  }

  .navbar__toggle {
    display: inherit;
  }
}

@media (max-width: 768px) {
  .navbar__title {
    display: none;
  }
}

@media (max-width: 640px) {
  [class^="searchHintContainer_"] {
    display: none;
  }
}

@media (max-width: 480px) {
  .header-github-link,
  .navbar [class*="toggleButton"] {
    display: none;
  }
}
```

Important: keep the yield order intact even if the exact breakpoint values need a small adjustment during QA.

- [ ] **Step 4: Keep fixed-size controls from collapsing**

```css
.navbar__toggle,
.header-github-link,
.navbar [class*="toggleButton"] {
  flex-shrink: 0;
}
```

- [ ] **Step 5: Add shell-level overflow protection if needed**

Update `src/theme/Navbar/Layout/styles.module.css` only if the shell still allows clipping or misalignment:

```css
.navbarChrome {
  min-width: 0;
}
```

Do not move `backdrop-filter` back onto `<nav>` itself.

- [ ] **Step 6: Run lint after the CSS/layout pass**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 7: Verify the flex layout manually across breakpoints**

Check at 640px, 768px, 996px, 1200px, and wide desktop:
- full search stays on the far right whenever it is inline
- no overlap between hamburger and search
- brand text hides before the right cluster becomes cramped
- no horizontal overflow or clipped controls
- spacing between right-side controls is consistent

- [ ] **Step 8: Commit Task 2**

```bash
git add src/css/custom.css src/theme/Navbar/Layout/styles.module.css
git commit -m "style: rebalance navbar flex layout"
```

### Task 3: Breadcrumb safety, modal polish, and production verification

**Files:**
- Modify: `src/components/navbar/ResponsiveSearch/styles.module.css`
- Modify: `src/css/custom.css`
- Modify: `src/theme/Navbar/Layout/styles.module.css` (only if breadcrumb/sticky spacing still needs correction)
- Test: manual QA on homepage and doc pages plus `npm run build`

**Interfaces:**
- Consumes: the responsive search controller from Task 1 and the flex-shell rules from Task 2
- Produces: final polished mobile/desktop behavior with no breadcrumb overlap and no regression in sticky/sidebar behavior

- [ ] **Step 1: Verify breadcrumb placement on doc pages with the new navbar height and modal behavior**

Manual check:
- open a documentation page with breadcrumbs
- scroll to ensure the sticky navbar still behaves correctly
- confirm breadcrumbs remain fully visible below the navbar in both light and dark themes

- [ ] **Step 2: Polish the modal and inline-search visuals to match the existing utility controls**

Use the same color system and motion language already present in `src/css/custom.css`:

```css
.compactTrigger {
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

.compactTrigger:hover {
  transform: translateY(-1px);
}
```

Mirror the dark-theme variants used by `.header-github-link` and `.navbar [class*='toggleButton']`.

- [ ] **Step 3: Verify the narrow-width top bar is exactly the approved set of controls**

Check at 320px, 360px, 390px, and 480px:
- hamburger is fully visible and clickable
- logo mark remains visible
- compact search trigger remains visible
- GitHub and theme toggle are no longer in the top row
- no clipped content or horizontal scroll appears

- [ ] **Step 4: Run the full project verification commands**

Run:
- `npm run typecheck`
- `npm run lint`
- `npm run build`

Expected: all PASS

- [ ] **Step 5: Fix any issue revealed by build or manual QA before finalizing**

Typical acceptable fixes in this step:
- small breakpoint-value adjustment while preserving the same yield order
- padding/alignment correction for the modal search panel
- right-cluster width-budget tuning if the field still feels cramped at a specific viewport

Do **not** add new features in this cleanup step.

- [ ] **Step 6: Commit Task 3**

```bash
git add src/components/navbar/ResponsiveSearch/styles.module.css src/css/custom.css src/theme/Navbar/Layout/styles.module.css
git commit -m "style: polish navbar responsive behavior"
```

## Self-Review Checklist

- **Spec coverage:**
  - three-zone flex shell: Task 2
  - right-aligned full search: Task 2
  - compact mobile search trigger + modal: Task 1
  - brand text yield order: Task 2
  - hide shortcut hint before compression: Task 2
  - hide GitHub/theme on narrow mobile: Task 2
  - breadcrumb safety and sticky-shell protection: Task 3
  - glassmorphism and purple-theme polish: Tasks 1 and 3
  - manual QA from 320px through desktop plus project checks: Tasks 1, 2, and 3
- **Placeholder scan:** no `TODO`, `TBD`, or undefined interfaces remain.
- **Type consistency:** `ResponsiveSearch` is the only new component interface introduced by name, and all tasks reference the same prop contract and compact-breakpoint behavior.
