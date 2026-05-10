import { translate } from "@docusaurus/Translate";
import { useNavbarMobileSidebar } from "@docusaurus/theme-common/internal";
import IconClose from "@theme/Icon/Close";
import NavbarLogo from "@theme/Navbar/Logo";
import clsx from "clsx";
import styles from "./styles.module.css";

function CloseButton({ className }) {
  const mobileSidebar = useNavbarMobileSidebar();
  return (
    <button
      type="button"
      aria-label={translate({
        id: "theme.docs.sidebar.closeSidebarButtonAriaLabel",
        message: "Close navigation bar",
        description: "The ARIA label for close button of mobile sidebar",
      })}
      className={clsx(
        "clean-btn",
        "navbar-sidebar__close",
        styles.closeButton,
        className,
      )}
      onClick={() => mobileSidebar.toggle()}
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
      <CloseButton />
    </div>
  );
}
