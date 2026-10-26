import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import HeroBanner from "@/components/HeroBanner";
import HomepageFeatures from "@/components/Homepage/Features";
import LatestNews from "@/components/LatestNews";

export default function Home({ homePageBlogMetadata, recentPosts }) {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Description will go into a meta tag in <head />"
    >
      <main className="background-grid background-grid--fade-out">
        <HeroBanner />
        <HomepageFeatures />
        <LatestNews
          recentPosts={recentPosts}
          homePageBlogMetadata={homePageBlogMetadata}
        />
      </main>
    </Layout>
  );
}
