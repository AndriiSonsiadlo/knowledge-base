import Link from "@docusaurus/Link";
import { translate } from "@docusaurus/Translate";
import { useColorMode, useThemeConfig } from "@docusaurus/theme-common";
import {
  useHideableNavbar,
  useNavbarMobileSidebar,
} from "@docusaurus/theme-common/internal";
import NavbarColorModeToggle from "@theme/Navbar/ColorModeToggle";
import type { Props } from "@theme/Navbar/Layout";
import NavbarMobileSidebar from "@theme/Navbar/MobileSidebar";
import clsx from "clsx";
import { BookOpen, Github, Menu, Moon, Search, Sun, X } from "lucide-react";
import React, { type ComponentProps, type ReactNode, useState } from "react";
import styles from "./styles.module.css";

function NavbarBackdrop(props: ComponentProps<"div">) {
  return (
    <div role="presentation" {...props} className="navbar-sidebar__backdrop" />
  );
}

function NavbarLogo() {
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <Link
      to="/"
      className="flex items-center gap-2 group cursor-pointer"
      style={{ textDecoration: "none" }}
    >
      <div
        className={clsx(
          "p-2 rounded-lg transition-all duration-300",
          isDarkTheme
            ? "bg-gradient-to-br from-purple-500/20 to-blue-500/20 group-hover:from-purple-500/40 group-hover:to-blue-500/40"
            : "bg-gradient-to-br from-purple-500/10 to-blue-500/10 group-hover:from-purple-500/20 group-hover:to-blue-500/20",
        )}
      >
        <BookOpen
          className={clsx(
            "w-6 h-6",
            isDarkTheme ? "text-purple-300" : "text-purple-600",
          )}
          viewBox="0 0 24 24"
        />
      </div>
      <span
        className={clsx(
          "text-lg font-bold transition-colors hidden sm:inline",
          isDarkTheme ? "text-white" : "text-slate-900",
        )}
      >
        Knowledge Base
      </span>
    </Link>
  );
}

export default function NavbarLayout({ children }: Props): ReactNode {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const {
    navbar: { hideOnScroll, style, items: navbarItems },
  } = useThemeConfig();
  const { colorMode, setColorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";
  const mobileSidebar = useNavbarMobileSidebar();
  const { navbarRef, isNavbarVisible } = useHideableNavbar(hideOnScroll);

  const toggleTheme = () => {
    setColorMode(isDarkTheme ? "light" : "dark");
  };
  const { siteConfig } = useDocusaurusContext();
  const { githubUrl } = siteConfig.customFields;
  return (
    <nav
      ref={navbarRef}
      aria-label={translate({
        id: "theme.NavBar.navAriaLabel",
        message: "Main",
        description: "The ARIA label for the main navigation",
      })}
      className={clsx(
        "navbar",
        "sticky top-0 z-50 backdrop-blur-xl transition-all duration-300",
        isDarkTheme
          ? "bg-slate-900/50 border-b border-white/10"
          : "bg-white/80 border-b border-slate-200",
        hideOnScroll && [
          styles.navbarHideable,
          !isNavbarVisible && styles.navbarHidden,
        ],
        {
          "navbar-sidebar--show": mobileSidebar.shown,
        },
      )}
    >
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <div className="flex-shrink-0">
            <NavbarLogo />
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex flex-1 items-center justify-center px-8">
            {children}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Search Bar - Desktop */}
            <div
              className={clsx(
                "hidden md:flex items-center gap-2 backdrop-blur-md rounded-lg px-3 py-2 transition-all",
                isDarkTheme
                  ? "bg-white/5 border border-white/10 hover:bg-white/10"
                  : "bg-slate-100/50 border border-slate-300 hover:bg-slate-100",
              )}
            >
              <Search
                className={clsx(
                  "w-4 h-4 flex-shrink-0",
                  isDarkTheme ? "text-slate-400" : "text-slate-500",
                )}
              />
              <input
                type="text"
                placeholder="Search docs..."
                className={clsx(
                  "bg-transparent outline-none text-sm w-40 placeholder-opacity-70 transition-colors",
                  isDarkTheme
                    ? "text-white placeholder-slate-500"
                    : "text-slate-900 placeholder-slate-400",
                )}
              />
            </div>

            {/* GitHub Link */}
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={clsx(
                "hidden sm:flex p-2 rounded-lg transition-all duration-300",
                isDarkTheme
                  ? "hover:bg-white/10 text-slate-400 hover:text-white"
                  : "hover:bg-slate-200 text-slate-600 hover:text-slate-900",
              )}
              aria-label="GitHub repository"
            >
              <Github className="w-5 h-5" />
            </a>

            {/* Theme Toggle */}
            <NavbarColorModeToggle className={styles.colorModeToggle} />

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className={clsx(
                "md:hidden p-2 rounded-lg transition-colors",
                isDarkTheme
                  ? "hover:bg-white/10 text-white"
                  : "hover:bg-slate-200 text-slate-900",
              )}
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div
            className={clsx(
              "md:hidden border-t py-4 space-y-2 backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-200",
              isDarkTheme ? "border-white/10" : "border-slate-200",
            )}
          >
            {children}

            {/* Mobile Actions */}
            <div
              className="flex items-center gap-2 px-2 pt-2 mt-2 border-t"
              style={{
                borderColor: isDarkTheme
                  ? "rgba(255,255,255,0.1)"
                  : "rgba(0,0,0,0.1)",
              }}
            >
              <button
                onClick={() => {
                  toggleTheme();
                  setIsMobileMenuOpen(false);
                }}
                className={clsx(
                  "flex-1 flex items-center justify-center gap-2 p-2 rounded-lg transition-all duration-300 font-medium",
                  isDarkTheme
                    ? "hover:bg-white/10 text-slate-400 hover:text-white"
                    : "hover:bg-slate-200 text-slate-600 hover:text-slate-900",
                )}
              >
                {isDarkTheme ? (
                  <>
                    <Sun className="w-4 h-4" />
                    <span>Light</span>
                  </>
                ) : (
                  <>
                    <Moon className="w-4 h-4" />
                    <span>Dark</span>
                  </>
                )}
              </button>
              <a
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={clsx(
                  "flex-1 flex items-center justify-center gap-2 p-2 rounded-lg transition-all duration-300 font-medium",
                  isDarkTheme
                    ? "hover:bg-white/10 text-slate-400 hover:text-white"
                    : "hover:bg-slate-200 text-slate-600 hover:text-slate-900",
                )}
              >
                <Github className="w-4 h-4" />
                <span>GitHub</span>
              </a>
            </div>
          </div>
        )}
      </div>

      <NavbarBackdrop onClick={mobileSidebar.toggle} />
      <NavbarMobileSidebar />
    </nav>
  );
}
