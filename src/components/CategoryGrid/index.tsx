import { useAllDocsData } from "@docusaurus/plugin-content-docs/client";
import { useThemeConfig } from "@docusaurus/theme-common";
import Heading from "@theme/Heading";
import type { ReactNode } from "react";
import CategoryCard from "../CategoryCard";
import styles from "./styles.module.css";

function shuffle<T>(arr: T[]): T[] {
  const array = [...arr]; // avoid mutating original
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

const colors: Category["color"][] = shuffle([
  "purple",
  "blue",
  "cyan",
  "green",
  "pink",
]);

interface Category {
  label: string;
  description: string;
  icon: string;
  href: string;
  color: "purple" | "blue" | "cyan" | "green" | "pink";
}

function useNavbarItems() {
  return useThemeConfig().navbar.items;
}

export default function CategoryGrid(): ReactNode {
  const rawCategories = useNavbarItems().filter(
    (item) =>
      item.type === "doc" ||
      item.type === "docSidebar" ||
      item.type === "docsVersion",
  );
  const allDocsData = useAllDocsData();
  const defaultDocsData = allDocsData.default ?? Object.values(allDocsData)[0];
  const sidebars = defaultDocsData?.versions[0]?.sidebars ?? {};
  const categories = rawCategories
    .map((item, index) => {
      const sidebarPath = item.sidebarId
        ? sidebars[item.sidebarId as string]?.link?.path
        : undefined;
      const href = item.href ?? item.to ?? sidebarPath;

      if (!href) {
        return null;
      }

      return {
        label: item.label,
        description: item.description,
        icon: item.icon,
        href,
        color: colors[index % colors.length],
      };
    })
    .filter(Boolean) as Category[];

  if (categories.length === 0) {
    return null;
  }

  return (
    <section className={styles.categoryGrid}>
      <div className="container">
        <div className="text-center mb-16">
          <Heading
            as="h1"
            className={`${styles.sectionTitle} font-display text-4xl md:text-5xl font-bold mb-4 leading-tight md:leading-snug`}
          >
            Categories
          </Heading>
          <p className={`${styles.sectionDescription} text-lg mx-auto`}>
            Explore comprehensive guides and structured learning paths across
            computer science, programming, and AI.
          </p>
        </div>

        <div className={styles.grid}>
          {categories.map((category, idx) => (
            <CategoryCard key={category.href} index={idx} {...category} />
          ))}
        </div>
      </div>
    </section>
  );
}
