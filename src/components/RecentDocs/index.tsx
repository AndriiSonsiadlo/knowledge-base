import GlassCard from "@components/GlassCard";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import Heading from "@theme/Heading";
import type { ReactNode } from "react";

interface RecentDocSummary {
  title: string;
  description?: string;
  permalink: string;
  lastUpdatedAt: number;
}

interface RecentDocsPluginData {
  docs?: RecentDocSummary[];
}

function formatRelativeDate(timestamp: number): string {
  const diffDays = Math.round((timestamp - Date.now()) / (1000 * 60 * 60 * 24));
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (Math.abs(diffDays) < 30) {
    return formatter.format(diffDays, "day");
  }

  const diffMonths = Math.round(diffDays / 30);
  if (Math.abs(diffMonths) < 12) {
    return formatter.format(diffMonths, "month");
  }

  return formatter.format(Math.round(diffMonths / 12), "year");
}

export default function RecentDocs(): ReactNode | null {
  const pluginData = usePluginData(
    "recent-docs-plugin",
  ) as RecentDocsPluginData | null;
  const docs = pluginData?.docs ?? [];

  if (docs.length === 0) {
    return null;
  }

  return (
    <section className="mx-auto w-full max-w-6xl pb-12 md:pb-16">
      <div className="mb-8 text-center">
        <Heading as="h2" className="font-display text-3xl md:text-4xl">
          Recently updated
        </Heading>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-700 dark:text-slate-300">
          The latest notes I’ve touched in this knowledge base.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {docs.map((doc) => (
          <GlassCard
            key={doc.permalink}
            className="h-full p-5 transition-transform duration-300 hover:-translate-y-1"
          >
            <Link
              to={doc.permalink}
              className="block h-full text-inherit no-underline"
            >
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--brand-accent)]">
                Updated {formatRelativeDate(doc.lastUpdatedAt)}
              </p>
              <Heading as="h3" className="mb-2 text-xl">
                {doc.title}
              </Heading>
              {doc.description ? (
                <p className="m-0 text-sm text-slate-700 dark:text-slate-300">
                  {doc.description}
                </p>
              ) : null}
            </Link>
          </GlassCard>
        ))}
      </div>
    </section>
  );
}
