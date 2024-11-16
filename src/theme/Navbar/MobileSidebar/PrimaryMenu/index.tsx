import { useColorMode, useThemeConfig } from "@docusaurus/theme-common";
import { useNavbarMobileSidebar } from "@docusaurus/theme-common/internal";
import NavbarItem, { type Props as NavbarItemConfig } from "@theme/NavbarItem";
import clsx from "clsx";
import React, { type ReactNode } from "react";

function useNavbarItems() {
  return useThemeConfig().navbar.items as NavbarItemConfig[];
}

export default function NavbarMobilePrimaryMenu(): ReactNode {
  const mobileSidebar = useNavbarMobileSidebar();
  const items = useNavbarItems();
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  // Filter out search and non-docSidebar items
  const filteredItems = items.filter(
    (item: any) => item.type === "docSidebar" && item.type !== "search",
  );

  return (
    <ul className={clsx("menu__list w-full p-2 space-y-1 flex-1")}>
      {filteredItems.length > 0 ? (
        filteredItems.map((item, i) => {
          return (
            <div
              className={clsx(
                "block px-4 py-3 rounded-lg transition-all duration-200 font-medium",
                isDarkTheme
                  ? "text-slate-300 hover:text-white hover:bg-purple-500/20 active:bg-purple-500/30"
                  : "text-slate-600 hover:text-slate-900 hover:bg-purple-100/50 active:bg-purple-100",
              )}
              onClick={() => mobileSidebar.toggle()}
            >
              <NavbarItem mobile key={i} {...item} />
            </div>
          );
        })
      ) : (
        <li className="list-none px-4 py-3">
          <p className={isDarkTheme ? "text-slate-500" : "text-slate-400"}>
            No items available
          </p>
        </li>
      )}
    </ul>
  );
}
