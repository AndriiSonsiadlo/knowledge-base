import GlassCard from "@components/GlassCard";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import type { ReactNode } from "react";

export default function HomeIntro(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  const githubUrl = siteConfig.customFields?.githubUrl as string | undefined;
  const avatarUrl = useBaseUrl("/img/photo.png");

  return (
    <section className="mx-auto mb-10 w-full max-w-5xl">
      <GlassCard className="p-6 md:p-7">
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <img
              src={avatarUrl}
              alt="Andrii Sonsiadlo"
              className="h-14 w-14 rounded-2xl border border-white/20 object-cover"
            />
            <div>
              <p className="mb-1 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--brand-primary)]">
                Andrii Sonsiadlo
              </p>
              <p className="m-0 text-sm text-slate-700 dark:text-slate-300">
                Software engineer — documenting what I learn about computer
                science and building things.
              </p>
            </div>
          </div>

          {githubUrl ? (
            <Link
              to={githubUrl}
              className="inline-flex items-center justify-center rounded-full bg-[var(--brand-primary)] px-4 py-2 text-sm font-semibold text-white no-underline transition hover:bg-[var(--brand-primary-dark)]"
            >
              View GitHub
            </Link>
          ) : null}
        </div>
      </GlassCard>
    </section>
  );
}
