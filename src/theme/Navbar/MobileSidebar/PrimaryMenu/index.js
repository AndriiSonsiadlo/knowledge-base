import { useThemeConfig } from "@docusaurus/theme-common";
import { useNavbarMobileSidebar } from "@docusaurus/theme-common/internal";
import NavbarItem from "@theme/NavbarItem";

// The primary menu displays the navbar items. The GitHub link is rendered
// separately in the sidebar header (see Navbar/MobileSidebar/Header), so
// it's excluded here to avoid showing it twice / stranding it below the
// category list.
export default function NavbarMobilePrimaryMenu() {
  const mobileSidebar = useNavbarMobileSidebar();
  const items = useThemeConfig().navbar.items.filter(
    (item) => item.className !== "header-github-link",
  );

  return (
    <ul className="menu__list">
      {items.map((item) => (
        <NavbarItem
          mobile
          {...item}
          onClick={() => mobileSidebar.toggle()}
          key={item.label ?? item.to ?? item.href}
        />
      ))}
    </ul>
  );
}
