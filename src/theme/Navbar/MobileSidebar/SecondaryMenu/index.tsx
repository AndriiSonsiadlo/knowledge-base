import React, { type ComponentProps, type ReactNode } from "react";
import { useThemeConfig } from "@docusaurus/theme-common";
import { useNavbarSecondaryMenu } from "@docusaurus/theme-common/internal";
import Translate from "@docusaurus/Translate";
import { ArrowLeft } from "lucide-react";
import clsx from "clsx";
import { useColorMode } from "@docusaurus/theme-common";

function SecondaryMenuBackButton(props: ComponentProps<"button">) {
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <button
      {...props}
      type="button"
      className={clsx(
        "clean-btn navbar-sidebar__back w-full",
        "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
        "font-medium text-sm",
        isDarkTheme
          ? "text-purple-300 hover:text-white hover:bg-purple-500/20 active:bg-purple-500/30"
          : "text-purple-600 hover:text-purple-900 hover:bg-purple-100/50 active:bg-purple-100",
      )}
    >
      <ArrowLeft className="w-4 h-4 flex-shrink-0" />
      <Translate
        id="theme.navbar.mobileSidebarSecondaryMenu.backButtonLabel"
        description="The label of the back button to return to main menu"
      >
        Back
      </Translate>
    </button>
  );
}

export default function NavbarMobileSidebarSecondaryMenu(): ReactNode {
  const isPrimaryMenuEmpty = useThemeConfig().navbar.items.length === 0;
  const secondaryMenu = useNavbarSecondaryMenu();
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <div
      className={clsx(
        "w-full flex flex-col gap-2 overflow-y-auto",
        isDarkTheme ? "bg-slate-900/50" : "bg-slate-50",
      )}
    >
      {!isPrimaryMenuEmpty && (
        <div className="p-2">
          <SecondaryMenuBackButton onClick={() => secondaryMenu.hide()} />
        </div>
      )}
      <div className="flex-1 overflow-y-auto px-2">{secondaryMenu.content}</div>
    </div>
  );
}
