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
import clsx from "clsx";
import styles from "./styles.module.css";

function useNavbarItems() {
  return useThemeConfig().navbar.items;
}

function NavbarItems({ items }) {
  return (
    <>
      {items.map((item, i) => (
        <ErrorCauseBoundary
          key={item.label ?? item.href ?? item.to ?? i}
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
  const [centerItems, utilityItems] = splitNavbarItems(items);
  const searchBarItem = items.find((item) => item.type === "search");

  return (
    <div className={styles.navbarInner}>
      <div
        className={clsx(
          "navbar__items",
          "navbar__items--brand",
          styles.brandRail,
        )}
      >
        {!mobileSidebar.disabled && <NavbarMobileSidebarToggle />}
        <NavbarLogo />
      </div>

      <div
        className={clsx(
          ThemeClassNames.layout.navbar.containerLeft,
          "navbar__items navbar__items--center",
          styles.centerRail,
        )}
      >
        <NavbarItems items={centerItems} />
      </div>

      <div
        className={clsx(
          ThemeClassNames.layout.navbar.containerRight,
          "navbar__items navbar__items--right",
          styles.utilityRail,
        )}
      >
        <NavbarItems items={utilityItems} />
        <NavbarColorModeToggle className={styles.colorModeToggle} />
        {!searchBarItem && (
          <NavbarSearch>
            <SearchBar />
          </NavbarSearch>
        )}
      </div>
    </div>
  );
}
