import Link from "@docusaurus/Link";
import clsx from "clsx";
import {
  Bot,
  Code2,
  Cpu,
  Database,
  Gamepad2,
  type LucideIcon,
  Plug,
  Rocket,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

const ICONS: Record<string, LucideIcon> = {
  code: Code2,
  cpu: Cpu,
  rocket: Rocket,
  plug: Plug,
  bot: Bot,
  database: Database,
  gamepad: Gamepad2,
};

interface CategoryCardProps {
  label: string;
  description: string;
  icon: string;
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
  const Icon = ICONS[icon] ?? Sparkles;

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
          <div className={clsx("flex-shrink-0", styles.cardIcon)}>
            <Icon size={26} strokeWidth={1.75} />
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
