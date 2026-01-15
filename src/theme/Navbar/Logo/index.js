import React from "react";
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
				className={clsx(
					"h-10 w-10 flex items-center justify-center rounded-lg transition-all duration-300",
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
