import { useAllDocsData } from "@docusaurus/plugin-content-docs/client";
import { useThemeConfig } from "@docusaurus/theme-common";
import type { ReactNode } from "react";
import { useCountUp } from "@/hooks/useCountUp";
import styles from "./styles.module.css";

function StatCard({ value, label }: { value: number; label: string }) {
  const animated = useCountUp(value);
  return (
    <div>
      <div className={styles.statValue}>{animated}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  );
}

export default function StatsSection(): ReactNode | null {
  const navbarItems = useThemeConfig().navbar.items;
  const categoryCount = navbarItems
    .flatMap((item) => (Array.isArray(item.items) ? item.items : [item]))
    .filter(
      (item) =>
        item.type === "doc" ||
        item.type === "docSidebar" ||
        item.type === "docsVersion",
    ).length;

  const allDocsData = useAllDocsData();
  const defaultDocsData = allDocsData.default ?? Object.values(allDocsData)[0];
  const docCount = defaultDocsData?.versions[0]?.docs.length ?? 0;

  if (categoryCount === 0 && docCount === 0) {
    return null;
  }

  return (
    <section className="mx-auto mb-10 w-full max-w-5xl">
      <div className={styles.stats}>
        <StatCard value={categoryCount} label="Categories" />
        <StatCard value={docCount} label="Documented topics" />
      </div>
    </section>
  );
}
