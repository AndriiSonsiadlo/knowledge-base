import CategoryGrid from "@components/CategoryGrid";
import GlassCard from "@components/GlassCard";
import HomeIntro from "@components/HomeIntro";
import RecentDocs from "@components/RecentDocs";
import ScrollReveal from "@components/ScrollReveal";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Heading from "@theme/Heading";
import Layout from "@theme/Layout";
import clsx from "clsx";
import type { ReactNode } from "react";

import styles from "./index.module.css";

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <div
        className={clsx(styles.heroGradient, "relative w-full overflow-hidden")}
      >
        {/* Animated background elements */}
        <div className={clsx(styles.heroBlob, styles.heroBlobPrimary)} />
        <div
          className={clsx(styles.heroBlob, styles.heroBlobAccent)}
          style={{ animationDelay: "3s, 0s" }}
        />
        <div
          className={clsx(styles.heroBlob, styles.heroBlobBlend)}
          style={{ animationDelay: "2s, 6s" }}
        />

        {/* Content */}
        <main className={clsx("container mx-auto px-4 relative z-10")}>
          {/* Header Section */}
          <div className="py-16 md:py-20 flex flex-col items-center justify-center">
            <GlassCard className="p-8 md:p-16 text-center w-full md:w-3/4 lg:w-2/3">
              <Heading
                as="h1"
                className={clsx(
                  styles.heroTitle,
                  "font-display mb-6 text-5xl font-bold leading-tight md:text-6xl md:leading-snug",
                )}
              >
                {siteConfig.title}
              </Heading>

              <div className="space-y-6 max-w-2xl mx-auto">
                <p
                  className={clsx(
                    styles.heroSubtitle,
                    "text-lg font-semibold md:text-xl",
                  )}
                >
                  A personal repository for mastering computer science and
                  software development.
                </p>

                <p
                  className={clsx(
                    styles.heroDescription,
                    "text-base leading-relaxed md:text-lg",
                  )}
                >
                  I’ve built this space to organize and document everything I’m
                  learning – from programming languages and computer science
                  fundamentals to data structures, algorithms, and machine
                  learning. Each section contains detailed explanations,
                  practical examples, and the insights I’ve gathered along the
                  way.
                </p>

                <div className="pt-4">
                  <p className={clsx(styles.heroCaption, "text-sm italic")}>
                    This is more than just notes – it’s my way of deepening
                    understanding, tracking progress, and sharing knowledge that
                    I find valuable. I use it to explore topics thoroughly,
                    experiment with code, and build a solid foundation in
                    computer science and software engineering.
                  </p>
                </div>
              </div>
            </GlassCard>
          </div>

          <ScrollReveal>
            <HomeIntro />
          </ScrollReveal>
          <ScrollReveal>
            <RecentDocs />
          </ScrollReveal>

          {/* Categories Section - Same Gradient */}
          <ScrollReveal>
            <div className="pb-16 md:pb-20">
              <GlassCard>
                <CategoryGrid />
              </GlassCard>
            </div>
          </ScrollReveal>
        </main>
      </div>
    </Layout>
  );
}
