import React, { version, type ReactNode } from "react";
import clsx from "clsx";
import { useNavbarSecondaryMenu } from "@docusaurus/theme-common/internal";
import { ThemeClassNames } from "@docusaurus/theme-common";
import type { Props } from "@theme/Navbar/MobileSidebar/Layout";
import { useColorMode } from "@docusaurus/theme-common";

function inertProps(inert: boolean) {
  const isBeforeReact19 = parseInt(version!.split(".")[0]!, 10) < 19;
  if (isBeforeReact19) {
    return inert ? { inert: true } : {};
  }
  return { inert };
}

function NavbarMobileSidebarPanel({
  children,
  inert,
}: {
  children: ReactNode;
  inert: boolean;
}) {
  return (
    <div
      className={clsx(
        ThemeClassNames.layout.navbar.mobileSidebar.panel,
        "navbar-sidebar__item menu",
        "transition-all duration-300",
      )}
      {...inertProps(inert)}
    >
      {children}
    </div>
  );
}

export default function NavbarMobileSidebarLayout({
  header,
  primaryMenu,
  secondaryMenu,
}: Props): ReactNode {
  const { shown: secondaryMenuShown } = useNavbarSecondaryMenu();
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <div
      className={clsx(
        ThemeClassNames.layout.navbar.mobileSidebar.container,
        "navbar-sidebar",
        "fixed inset-0 top-16 z-40 flex flex-col",
        isDarkTheme
          ? "bg-slate-950 border-r border-white/10"
          : "bg-white border-r border-slate-200",
      )}
    >
      {header}
      <div
        className={clsx(
          "navbar-sidebar__items flex-1 overflow-y-auto",
          "flex transition-transform duration-300",
          {
            "navbar-sidebar__items--show-secondary": secondaryMenuShown,
          },
        )}
      >
        <NavbarMobileSidebarPanel inert={secondaryMenuShown}>
          {primaryMenu}
        </NavbarMobileSidebarPanel>
        <NavbarMobileSidebarPanel inert={!secondaryMenuShown}>
          {secondaryMenu}
        </NavbarMobileSidebarPanel>
      </div>
    </div>
  );
}
