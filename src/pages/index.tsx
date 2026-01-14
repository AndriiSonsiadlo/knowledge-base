import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import CategoryGrid from "@components/CategoryGrid";
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
				className={clsx(styles.heroGradient, "w-full relative overflow-hidden")}
			>
				{/* Animated background elements */}
				<div className="absolute top-0 left-0 w-lg h-128 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
				<div
					className="absolute top-20 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"
					style={{ animationDelay: "3s" }}
				></div>
				<div
					className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"
					style={{ animationDelay: "2s" }}
				></div>

				{/* Content */}
				<main className={clsx("container mx-auto px-4 relative z-10")}>
					{/* Header Section */}
					<div className="py-16 md:py-20 flex flex-col items-center justify-center">
						<div
							className={clsx(
								styles.glassCard,
								"p-8 md:p-16 rounded-3xl text-center w-full md:w-3/4 lg:w-2/3",
							)}
						>
							<Heading
								as="h1"
								className="text-5xl md:text-6xl font-bold mb-6 bg-clip-text drop-shadow-lg text-transparent bg-gradient-to-r from-purple-400 via-blue-300 to-purple-300 dark:from-purple-600 dark:via-blue-400 dark:to-purple-700 leading-tight md:leading-snug"
							>
								{siteConfig.title}
							</Heading>

							<div className="space-y-6 max-w-2xl mx-auto">
								<p className="text-lg md:text-xl font-semibold">
									A personal repository for mastering computer science and
									software development.
								</p>

								<p className="text-base md:text-lg leading-relaxed">
									I’ve built this space to organize and document everything I’m
									learning – from programming languages and computer science
									fundamentals to data structures, algorithms, and machine
									learning. Each section contains detailed explanations,
									practical examples, and the insights I’ve gathered along the
									way.
								</p>

								<div className="pt-4">
									<p className="text-sm text-slate-400 italic">
										This is more than just notes – it’s my way of deepening
										understanding, tracking progress, and sharing knowledge that
										I find valuable. I use it to explore topics thoroughly,
										experiment with code, and build a solid foundation in
										computer science and software engineering.
									</p>
								</div>
							</div>
						</div>
					</div>

					{/* Categories Section - Same Gradient */}
					<div className="pb-16 md:pb-20">
						<div className={styles.glassCard}>
							<CategoryGrid />
						</div>
					</div>
				</main>
			</div>
		</Layout>
	);
}
