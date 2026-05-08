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
      className="navbar__brand group cursor-pointer"
      style={{ textDecoration: "none" }}
    >
      <div
        className="navbar__brand-mark"
        style={{
          background: isDarkTheme
            ? "linear-gradient(135deg, rgb(var(--brand-primary-rgb) / 0.18), rgb(var(--brand-accent-rgb) / 0.18))"
            : "linear-gradient(135deg, rgb(var(--brand-primary-rgb) / 0.1), rgb(var(--brand-accent-rgb) / 0.1))",
        }}
      >
        <BookOpen
          className="h-[18px] w-[18px]"
          style={{
            color: isDarkTheme
              ? "var(--brand-primary-light)"
              : "var(--brand-primary-dark)",
          }}
        />
      </div>

      <span
        className={clsx(
          "navbar__title transition-colors hidden sm:inline",
          isDarkTheme ? "text-white" : "text-slate-900",
        )}
      >
        Knowledge Base
      </span>
    </Link>
  );
}
