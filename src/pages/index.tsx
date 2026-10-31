import Link from "@docusaurus/Link";
import { useAllDocsData } from "@docusaurus/plugin-content-docs/client";
import { useThemeConfig } from "@docusaurus/theme-common";
import useBaseUrl from "@docusaurus/useBaseUrl";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { usePluginData } from "@docusaurus/useGlobalData";
import Layout from "@theme/Layout";
import {
  Binary,
  Boxes,
  Braces,
  CircuitBoard,
  Cpu,
  Database,
  FileCode,
  Gamepad2,
  type LucideIcon,
  Sparkles,
  Terminal,
} from "lucide-react";
import type { ReactNode } from "react";

import { useCountUp } from "../hooks/useCountUp";

import styles from "./index.module.css";

// Home page in the Workbench style (mockups/ide): one reading column, mono
// chrome, `>` section markers, flat surface cards. Sections come from the
// navbar config so this page never drifts from the site navigation.

interface NavItem {
  type?: string;
  label?: string;
  description?: string;
  sidebarId?: string;
  to?: string;
  href?: string;
  items?: NavItem[];
}

interface Section {
  id?: string;
  label: string;
  description?: string;
  href: string;
}

interface SectionGroup {
  label: string;
  sections: Section[];
}

interface RecentDoc {
  title: string;
  description?: string;
  permalink: string;
  lastUpdatedAt: number;
  section: string;
}

const isDocItem = (item: NavItem) =>
  item.type === "doc" ||
  item.type === "docSidebar" ||
  item.type === "docsVersion";

function useSectionGroups(): { groups: SectionGroup[]; docCount: number } {
  const items = useThemeConfig().navbar.items as NavItem[];
  const allDocsData = useAllDocsData();
  const docs = allDocsData.default ?? Object.values(allDocsData)[0];
  const version = docs?.versions[0];
  const sidebars = version?.sidebars ?? {};

  const toSection = (item: NavItem): Section | null => {
    const href =
      item.href ??
      item.to ??
      (item.sidebarId ? sidebars[item.sidebarId]?.link?.path : undefined);
    return href && item.label
      ? {
          id: item.sidebarId,
          label: item.label,
          description: item.description,
          href,
        }
      : null;
  };

  // A top-level doc item is its own one-card group; a dropdown is a group.
  const groups = items
    .map((item): SectionGroup | null => {
      if (Array.isArray(item.items)) {
        const sections = item.items
          .filter(isDocItem)
          .map(toSection)
          .filter(Boolean) as Section[];
        return sections.length ? { label: item.label ?? "", sections } : null;
      }
      if (!isDocItem(item)) return null;
      const section = toSection(item);
      return section ? { label: section.label, sections: [section] } : null;
    })
    .filter(Boolean) as SectionGroup[];

  // Generated category index pages ("/category/…") are not written pages.
  const docCount =
    version?.docs.filter((d) => !d.id.startsWith("/category/")).length ?? 0;
  return { groups, docCount };
}

const SECTION_LABELS: Record<string, string> = {
  programming: "Programming",
  "game-development": "Game Development",
  "computer-science": "Computer Science",
  "data-tools": "Data Science",
  "machine-learning": "Machine Learning",
  "gpu-computing": "GPU & Accelerators",
  embedded: "Embedded Systems",
  linux: "Linux & Kernel",
};

const sectionLabel = (section: string) =>
  SECTION_LABELS[section] ??
  section
    .split("-")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");

const dateFormatter = new Intl.DateTimeFormat("en", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

// Decorative section glyphs (lucide, 1.5 stroke); keyed by navbar sidebarId.
const SECTION_ICONS: Record<string, LucideIcon> = {
  cppSidebar: Braces,
  cppLibrariesSidebar: Boxes,
  pythonSidebar: FileCode,
  computerScienceSidebar: Binary,
  gpuComputingSidebar: Cpu,
  embeddedSidebar: CircuitBoard,
  linuxSidebar: Terminal,
  machineLearningSidebar: Sparkles,
  dataToolsSidebar: Database,
  gameDevSidebar: Gamepad2,
};

function Stat({ value, label }: { value: number; label: string }) {
  const [shown, ref] = useCountUp<HTMLDivElement>(value);
  return (
    <div ref={ref} className={styles.stat}>
      <dt className={styles.statLabel}>{label}</dt>
      <dd className={styles.statValue}>{shown}</dd>
    </div>
  );
}

function SectionCards({ sections }: { sections: Section[] }) {
  return (
    <ul className={styles.cards}>
      {sections.map((s) => {
        const Icon = s.id ? SECTION_ICONS[s.id] : undefined;
        return (
          <li key={s.href}>
            <Link to={s.href}>
              {Icon ? (
                <Icon
                  className={styles.cardIcon}
                  size={20}
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              ) : null}
              <strong>{s.label}</strong>
              {s.description ? <span>{s.description}</span> : null}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  const githubUrl = siteConfig.customFields?.githubUrl as string | undefined;
  const avatarUrl = useBaseUrl("/img/photo.png");
  const { groups, docCount } = useSectionGroups();
  const sectionCount = groups.reduce((n, g) => n + g.sections.length, 0);
  const recent =
    (usePluginData("recent-docs-plugin") as { docs?: RecentDoc[] } | null)
      ?.docs ?? [];

  // Single-section groups (Game Development) render together
  // under "Sections"; dropdown groups get their own `###` heading.
  const singles = groups.filter((g) => g.sections.length === 1);
  const multis = groups.filter((g) => g.sections.length > 1);

  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <main className={styles.page}>
        <article className={styles.article}>
          <ol className={styles.crumbs} aria-label="Breadcrumb">
            <li aria-current="page">~/knowledge-base</li>
          </ol>

          <h1 className={styles.title}>Knowledge Base</h1>
          <p className={styles.meta}>
            <span>by Andrii Sonsiadlo</span>
          </p>

          <p className={styles.lede}>
            A personal repository for mastering computer science and software
            development. I’ve built this space to organize and document
            everything I’m learning – from programming languages and computer
            science fundamentals to data structures, algorithms, and machine
            learning.
          </p>

          <dl className={styles.stats} aria-label="Site statistics">
            <Stat value={docCount} label="pages" />
            <Stat value={sectionCount} label="sections" />
            <Stat value={groups.length} label="areas" />
          </dl>

          <div className={styles.admonition} role="note">
            <p className={styles.admTitle}>How it’s organized</p>
            <p>
              Each section is a path: pages build on the ones before them, and
              every concept has one home that other pages link to. Press{" "}
              <code>Ctrl K</code> to search all notes.
            </p>
          </div>

          <h2 id="sections">Sections</h2>
          <SectionCards sections={singles.flatMap((g) => g.sections)} />
          {multis.map((g) => (
            <section key={g.label}>
              <h3 id={g.label.toLowerCase().replace(/[^a-z]+/g, "-")}>
                {g.label}
              </h3>
              <SectionCards sections={g.sections} />
            </section>
          ))}

          {recent.length > 0 && (
            <>
              <h2 id="recent">Recently updated</h2>
              <ul className={styles.cards}>
                {recent.map((doc) => (
                  <li key={doc.permalink}>
                    <Link to={doc.permalink}>
                      <small className={styles.cardMeta}>
                        {sectionLabel(doc.section)} ·{" "}
                        {dateFormatter.format(new Date(doc.lastUpdatedAt))}
                      </small>
                      <strong>{doc.title}</strong>
                      {doc.description ? <span>{doc.description}</span> : null}
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h2 id="about">About</h2>
          <div className={styles.about}>
            <img src={avatarUrl} alt="Andrii Sonsiadlo" />
            <p>
              Software engineer – documenting what I learn about computer
              science and building things. This is more than notes: it’s how I
              deepen understanding, track progress, and share what I find
              valuable.
            </p>
            {githubUrl ? (
              <Link to={githubUrl} className={styles.aboutLink}>
                github ↗
              </Link>
            ) : null}
          </div>
        </article>
      </main>
    </Layout>
  );
}
