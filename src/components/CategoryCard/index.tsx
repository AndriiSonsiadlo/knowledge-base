import Link from "@docusaurus/Link";
import clsx from "clsx";
import type React from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

interface CategoryCardProps {
	label: string;
	description: string;
	icon: React.ReactNode;
	href: string;
	color: "purple" | "blue" | "cyan" | "green" | "pink";
	index?: number;
}

export default function CategoryCard({
	label,
	description,
	icon,
	href,
	color = "purple",
	index = 0,
}: CategoryCardProps): ReactNode {
	return (
		<Link to={href} className={clsx(styles.cardLink, "no-underline")}>
			<div
				className={clsx(
					"rounded-2xl p-8 transition-all duration-300 cursor-pointer h-full shadow-md",
					"hover:-translate-y-1",
					styles.categoryCard,
					styles[`card-${color}`],
				)}
				style={{ animationDelay: `${index * 90}ms` }}
			>
				<div className="flex items-start gap-4 h-full">
					<div className={clsx("text-4xl flex-shrink-0", styles.cardIcon)}>
						{icon}
					</div>
					<div className="flex-1">
						<h3 className={styles.cardTitle}>{label}</h3>
						<p className={styles.cardDescription}>{description}</p>
					</div>
				</div>
			</div>
		</Link>
	);
}
