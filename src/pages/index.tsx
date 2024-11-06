import type {ReactNode} from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";
import HomepageFeatures from "@site/src/components/HomepageFeatures";

import styles from "./index.module.css";

function HomepageHeader(): ReactNode {
    const {siteConfig} = useDocusaurusContext();
    return (
        <div
            className={clsx(
                styles.heroGradient,
                "min-h-screen w-full flex flex-col items-center justify-start pt-28 pb-20"
            )}
        >
            {/* Glass Header */}
            <div className="container flex justify-center mb-16">
                <div
                    className={clsx(styles.glassCard, "p-10 rounded-3xl text-center w-full md:w-2/3")}>
                    <Heading as="h1" className="text-5xl font-bold mb-4">
                        {siteConfig.title}
                    </Heading>

                    <p className="text-lg opacity-90 mb-6">{siteConfig.tagline}</p>

                    <Link
                        className={clsx("button button--secondary button--lg", styles.glassButton)}
                        to="/docs/intro"
                    >
                        My Base Knowledge
                    </Link>
                </div>
            </div>

            {/* Features inside the gradient */}
            <HomepageFeatures/>
        </div>
    );
}

export default function Home(): ReactNode {
    const {siteConfig} = useDocusaurusContext();
    return (
        <Layout
            title={`Hello from ${siteConfig.title}`}
            description="Description will go into a meta tag in <head />"
        >
            <HomepageHeader/>
        </Layout>
    );
}
