import { useLayoutDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import { useThemeConfig } from "@docusaurus/theme-common";
import React, { type ReactNode } from "react";
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
  const categories = rawCategories.map((item, index) => {
    const sidebarLink = useLayoutDocsSidebar(
      (item.sidebarId as string) || (item.docId as string),
      item.docsPluginId as string,
    ).link;
    return {
      label: item.label,
      description: item.description,
      icon: item.icon,
      href: item.href ?? sidebarLink.path,
      color: colors[index % colors.length],
    };
  }) as Category[];

  if (categories.length === 0) {
    return null;
  }

  return (
    <section className={styles.categoryGrid}>
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-slate-100 drop-shadow-lg">
            Knowledge Categories
          </h2>
          <p className="text-lg text-[var(--ifm-color-text-secondary)] drop-shadow mx-auto">
            Explore comprehensive guides and structured learning paths across
            computer science, programming, and AI.
          </p>
        </div>

        <div className={styles.grid}>
          {categories.map((category, idx) => (
            <CategoryCard key={idx} {...category} />
          ))}
        </div>
      </div>
    </section>
  );
}
