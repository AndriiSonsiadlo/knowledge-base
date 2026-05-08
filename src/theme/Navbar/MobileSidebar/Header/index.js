import { translate } from "@docusaurus/Translate";
import { useThemeConfig } from "@docusaurus/theme-common";
import { useNavbarMobileSidebar } from "@docusaurus/theme-common/internal";
import IconClose from "@theme/Icon/Close";
import NavbarColorModeToggle from "@theme/Navbar/ColorModeToggle";
import NavbarLogo from "@theme/Navbar/Logo";
import clsx from "clsx";

function CloseButton() {
  const mobileSidebar = useNavbarMobileSidebar();
  return (
    <button
      type="button"
      aria-label={translate({
        id: "theme.docs.sidebar.closeSidebarButtonAriaLabel",
        message: "Close navigation bar",
        description: "The ARIA label for close button of mobile sidebar",
      })}
      className="clean-btn navbar-sidebar__close"
      onClick={() => mobileSidebar.toggle()}
    >
      <IconClose color="var(--ifm-color-emphasis-600)" />
    </button>
  );
}

// The GitHub link is rendered here (sidebar header) instead of in the
// primary menu list, so it stays part of the sidebar's navigation chrome
// rather than showing up as one more row below every category link.
function GitHubLink() {
  const { navbar } = useThemeConfig();
  const githubItem = navbar.items.find(
    (item) => item.className === "header-github-link",
  );

  if (!githubItem?.href) {
    return null;
  }

  const label = githubItem["aria-label"] ?? "GitHub repository";

  return (
    <a
      href={githubItem.href}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx("header-github-link", "margin-right--sm")}
      aria-label={label}
    >
      <span className="sr-only">{label}</span>
    </a>
  );
}

export default function NavbarMobileSidebarHeader() {
  return (
    <div className="navbar-sidebar__brand">
      <NavbarLogo />
      <GitHubLink />
      <NavbarColorModeToggle className="margin-right--md" />
      <CloseButton />
    </div>
  );
}
