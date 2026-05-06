import clsx from "clsx";
import React from "react";
import {
  ErrorCauseBoundary,
  ThemeClassNames,
  useThemeConfig,
} from "@docusaurus/theme-common";
import {
  splitNavbarItems,
  useNavbarMobileSidebar,
} from "@docusaurus/theme-common/internal";
import NavbarColorModeToggle from "@theme/Navbar/ColorModeToggle";
import NavbarLogo from "@theme/Navbar/Logo";
import NavbarMobileSidebarToggle from "@theme/Navbar/MobileSidebar/Toggle";
import NavbarSearch from "@theme/Navbar/Search";
import NavbarItem from "@theme/NavbarItem";
import SearchBar from "@theme/SearchBar";
import styles from "./styles.module.css";

function useNavbarItems() {
  return useThemeConfig().navbar.items;
}

function NavbarItems({ items }) {
  return (
    <>
      {items.map((item, index) => (
        <ErrorCauseBoundary
          key={index}
          onError={(error) =>
            new Error(
              `A theme navbar item failed to render.
Please double-check the following navbar item (themeConfig.navbar.items) of your Docusaurus config:
${JSON.stringify(item, null, 2)}`,
              { cause: error },
            )
          }
        >
          <NavbarItem {...item} />
        </ErrorCauseBoundary>
      ))}
    </>
  );
}

export default function NavbarContent() {
  const mobileSidebar = useNavbarMobileSidebar();
  const items = useNavbarItems();
  const [leftItems, rightItems] = splitNavbarItems(items);
  const searchBarItem = items.find((item) => item.type === "search");

  return (
    <div className={clsx("navbar__inner", styles.navbarInner)}>
      <div
        className={clsx(
          ThemeClassNames.layout.navbar.containerLeft,
          "navbar__items",
          styles.brandRail,
        )}
      >
        {!mobileSidebar.disabled && <NavbarMobileSidebarToggle />}
        <NavbarLogo />
      </div>

      <div className={clsx("navbar__items", styles.navRail)}>
        <div className={styles.desktopNav}>
          <NavbarItems items={leftItems} />
        </div>
      </div>

      <div
        className={clsx(
          ThemeClassNames.layout.navbar.containerRight,
          "navbar__items navbar__items--right",
          styles.actionRail,
        )}
      >
        <div className={styles.utilityGroup}>
          <NavbarItems items={rightItems} />
          <NavbarColorModeToggle className={styles.colorModeToggle} />
        </div>
        {!searchBarItem && (
          <NavbarSearch>
            <SearchBar />
          </NavbarSearch>
        )}
      </div>
    </div>
  );
}
