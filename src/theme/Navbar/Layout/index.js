import { translate } from "@docusaurus/Translate";
import { ThemeClassNames, useThemeConfig } from "@docusaurus/theme-common";
import {
  useHideableNavbar,
  useNavbarMobileSidebar,
} from "@docusaurus/theme-common/internal";
import NavbarMobileSidebar from "@theme/Navbar/MobileSidebar";
import clsx from "clsx";
import { useEffect, useState } from "react";
import styles from "./styles.module.css";

function NavbarBackdrop(props) {
  return (
    <div
      role="presentation"
      {...props}
      className={clsx("navbar-sidebar__backdrop", props.className)}
    />
  );
}
export default function NavbarLayout({ children }) {
  const {
    navbar: { hideOnScroll, style },
  } = useThemeConfig();
  const mobileSidebar = useNavbarMobileSidebar();
  const { navbarRef, isNavbarVisible } = useHideableNavbar(hideOnScroll);
  const [hasScrolled, setHasScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setHasScrolled(window.scrollY > 40);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      ref={navbarRef}
      aria-label={translate({
        id: "theme.NavBar.navAriaLabel",
        message: "Main",
      })}
      className={clsx(
        ThemeClassNames.layout.navbar.container,
        "navbar",
        "sticky top-0 z-50",
        hideOnScroll && [
          styles.navbarHideable,
          !isNavbarVisible && styles.navbarHidden,
        ],
        {
          "navbar--dark": style === "dark",
          "navbar--primary": style === "primary",
          "navbar-sidebar--show": mobileSidebar.shown,
          "shadow-none": !hasScrolled,
          [styles.navbarScrolled]: hasScrolled,
        },
      )}
    >
      {/* backdrop-filter lives on this inner wrapper, not on <nav> itself:
			    backdrop-filter (like filter/transform) creates a new containing
			    block for position:fixed descendants, which would break the
			    full-viewport fixed positioning of NavbarBackdrop/NavbarMobileSidebar
			    below (they'd size themselves against the navbar's own box instead
			    of the viewport, collapsing the mobile sidebar to nothing). */}
      <div className={styles.navbarChrome}>
        <div className={styles.navbarContent}>{children}</div>
      </div>
      <NavbarBackdrop onClick={mobileSidebar.toggle} />
      <NavbarMobileSidebar />
    </nav>
  );
}
