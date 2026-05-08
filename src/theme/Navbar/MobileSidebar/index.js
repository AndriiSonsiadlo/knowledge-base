import {
  useLockBodyScroll,
  useNavbarMobileSidebar,
} from "@docusaurus/theme-common/internal";
import NavbarMobileSidebarHeader from "@theme/Navbar/MobileSidebar/Header";
import NavbarMobileSidebarLayout from "@theme/Navbar/MobileSidebar/Layout";
import NavbarMobileSidebarPrimaryMenu from "@theme/Navbar/MobileSidebar/PrimaryMenu";
import NavbarMobileSidebarSecondaryMenu from "@theme/Navbar/MobileSidebar/SecondaryMenu";

export default function NavbarMobileSidebar() {
  const mobileSidebar = useNavbarMobileSidebar();
  useLockBodyScroll(mobileSidebar.shown);

  // Docusaurus only mounts this panel when its own hardcoded 996px
  // "mobile" breakpoint matches (mobileSidebar.shouldRender), but this site
  // switches to the hamburger toggle earlier than that (see the
  // `.navbar__toggle` override in custom.css). Without this, opening the
  // menu between ~997px and that wider breakpoint showed the backdrop with
  // no sidebar panel, because the panel simply never mounted. Rendering it
  // whenever it's actually open (not just when Docusaurus thinks we're on
  // mobile) keeps the toggle functional at every width it's visible.
  if (!mobileSidebar.shouldRender && !mobileSidebar.shown) {
    return null;
  }

  return (
    <NavbarMobileSidebarLayout
      header={<NavbarMobileSidebarHeader />}
      primaryMenu={<NavbarMobileSidebarPrimaryMenu />}
      secondaryMenu={<NavbarMobileSidebarSecondaryMenu />}
    />
  );
}
