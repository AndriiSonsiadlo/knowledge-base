import React, { type ReactNode } from "react";
import { useColorMode, useThemeConfig } from "@docusaurus/theme-common";
import type { Props } from "@theme/Navbar/ColorModeToggle";
import clsx from "clsx";
import { Moon, Sun } from "lucide-react";

export default function NavbarColorModeToggle({ className }: Props): ReactNode {
  const navbarStyle = useThemeConfig().navbar.style;
  const { disableSwitch, respectPrefersColorScheme } =
    useThemeConfig().colorMode;
  const { colorModeChoice, colorMode, setColorMode } = useColorMode();

  if (disableSwitch) {
    return null;
  }

  const isDarkTheme = colorMode === "dark";
  const toggleTheme = () => {
    setColorMode(isDarkTheme ? "light" : "dark");
  };

  return (
    <>
      {/*<ColorModeToggle*/}
      {/*    className={clsx(*/}
      {/*        'hidden sm:flex p-2 rounded-lg transition-all duration-300',*/}
      {/*        isDarkTheme*/}
      {/*            ? 'hover:bg-white/10 text-slate-400 hover:text-white'*/}
      {/*            : 'hover:bg-slate-200 text-slate-600 hover:text-slate-900'*/}
      {/*    )}*/}
      {/*    buttonClassName={*/}
      {/*        navbarStyle === 'dark' ? styles.darkNavbarColorModeToggle : undefined*/}
      {/*    }*/}
      {/*    respectPrefersColorScheme={respectPrefersColorScheme}*/}
      {/*    value={colorModeChoice}*/}
      {/*    onChange={toggleTheme}*/}
      {/*/>*/}

      <button
        onClick={toggleTheme}
        className={clsx(
          "hidden sm:flex p-2 rounded-lg transition-all duration-300",
          isDarkTheme
            ? "hover:bg-white/10 text-slate-400 hover:text-white"
            : "hover:bg-slate-200 text-slate-600 hover:text-slate-900",
        )}
        aria-label="Toggle theme"
      >
        {isDarkTheme ? (
          <Sun className="w-5 h-5" />
        ) : (
          <Moon className="w-5 h-5" />
        )}
      </button>
    </>
  );
}
