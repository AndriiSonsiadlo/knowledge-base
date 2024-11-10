import React, { type ReactNode } from "react";
import { useNavbarMobileSidebar } from "@docusaurus/theme-common/internal";
import { translate } from "@docusaurus/Translate";
import NavbarColorModeToggle from "@theme/Navbar/ColorModeToggle";
import IconClose from "@theme/Icon/Close";
import NavbarLogo from "@theme/Navbar/Logo";
import { useColorMode } from "@docusaurus/theme-common";
import clsx from "clsx";
import { X } from "lucide-react";

function CloseButton() {
  const mobileSidebar = useNavbarMobileSidebar();
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <button
      type="button"
      aria-label={translate({
        id: "theme.docs.sidebar.closeSidebarButtonAriaLabel",
        message: "Close navigation bar",
        description: "The ARIA label for close button of mobile sidebar",
      })}
      className={clsx(
        "p-2 rounded-lg transition-all duration-300",
        isDarkTheme
          ? "hover:bg-white/10 text-slate-400 hover:text-white"
          : "hover:bg-slate-200 text-slate-600 hover:text-slate-900",
      )}
      onClick={() => mobileSidebar.toggle()}
    >
      <X className="w-6 h-6" />
    </button>
  );
}

export default function NavbarMobileSidebarHeader(): ReactNode {
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <div
      className={clsx(
        "navbar-sidebar__brand flex items-center justify-between p-4 border-b flex-shrink-0",
        isDarkTheme ? "border-white/10" : "border-slate-200",
      )}
    >
      <NavbarLogo />
      <div className="flex items-center gap-2">
        <NavbarColorModeToggle />
        <CloseButton />
      </div>
    </div>
  );
}
