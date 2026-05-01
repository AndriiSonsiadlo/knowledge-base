import Link from "@docusaurus/Link";
import { useColorMode } from "@docusaurus/theme-common";
import clsx from "clsx";
import { BookOpen } from "lucide-react";

export default function NavbarLogo() {
  const { colorMode } = useColorMode();
  const isDarkTheme = colorMode === "dark";

  return (
    <Link
      to="/knowledge-base/"
      className="navbar__brand flex items-center gap-2 group cursor-pointer"
      style={{ textDecoration: "none" }}
    >
      <div
        className="flex h-10 w-10 items-center justify-center rounded-lg transition-all duration-300 group-hover:scale-105"
        style={{
          background: isDarkTheme
            ? "linear-gradient(135deg, rgb(var(--brand-primary-rgb) / 0.22), rgb(var(--brand-accent-rgb) / 0.22))"
            : "linear-gradient(135deg, rgb(var(--brand-primary-rgb) / 0.12), rgb(var(--brand-accent-rgb) / 0.12))",
        }}
      >
        <BookOpen
          className="h-6 w-6"
          style={{
            color: isDarkTheme
              ? "var(--brand-primary-light)"
              : "var(--brand-primary-dark)",
          }}
        />
      </div>

      <span
        className={clsx(
          "navbar__title text-lg font-bold transition-colors hidden sm:inline",
          isDarkTheme ? "text-white" : "text-slate-900",
        )}
      >
        Knowledge Base
      </span>
    </Link>
  );
}
