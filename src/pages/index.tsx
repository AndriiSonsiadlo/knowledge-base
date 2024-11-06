// import type {ReactNode} from 'react';
// import clsx from 'clsx';
// import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
// import HomepageFeatures from '@site/src/components/HomepageFeatures';
// import Heading from '@theme/Heading';
//
// import styles from './index.module.css';
//
// function HomepageHeader() {
//   const {siteConfig} = useDocusaurusContext();
//   return (
//     <header className={clsx('hero hero--primary', styles.heroBanner)}>
//       <div className="container">
//         <Heading as="h1" className="hero__title">
//           {siteConfig.title}
//         </Heading>
//         <p className="hero__subtitle">{siteConfig.tagline}</p>
//         <div className={styles.buttons}>
//           <Link
//             className="button button--secondary button--lg"
//             to="/docs/intro">
//             My Base Knowledge
//           </Link>
//         </div>
//       </div>
//     </header>
//   );
// }
//
// export default function Home(): ReactNode {
//   const {siteConfig} = useDocusaurusContext();
//   return (
//     <Layout
//       title={`Hello from ${siteConfig.title}`}
//       description="Description will go into a meta tag in <head />">
//       <HomepageHeader />
//       <main>
//         <HomepageFeatures />
//       </main>
//     </Layout>
//   );
// }

import React from 'react';
import {Search, BookOpen, Zap, BarChart3} from 'lucide-react';
import Navbar from "@site/src/components/Navbar";

export default function Homepage() {
    const {siteConfig} = useDocusaurusContext();

    const features = [
        {
            icon: BookOpen,
            title: 'Organized Knowledge',
            description: 'Structured notes and information organized by categories'
        },
        {
            icon: Search,
            title: 'Powerful Search',
            description: 'Find what you need instantly with full-text search'
        },
        {
            icon: Zap,
            title: 'Lightning Fast',
            description: 'Optimized performance for seamless browsing'
        },
        {
            icon: BarChart3,
            title: 'Always Growing',
            description: 'Continuously updated with new insights'
        }
    ];

    return (
        <Layout
            title={`Hello from ${siteConfig.title}`}
            description="Description will go into a meta tag in <head />">
            <div
                className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
                {/*<Navbar/>*/}

                {/* Animated background elements */}
                <div
                    className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
                <div
                    className="absolute top-20 right-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"
                    style={{animationDelay: '2s'}}></div>
                <div
                    className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"
                    style={{animationDelay: '4s'}}></div>

                {/* Content */}
                <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Navigation */}
                    <nav
                        className="backdrop-blur-md bg-white/5 border border-white/10 rounded-full px-6 py-3 inline-flex items-center gap-2 mt-6 hover:bg-white/10 transition-all duration-300">
                        <BookOpen className="w-5 h-5 text-purple-400"/>
                        <span className="text-white font-semibold">Knowledge Base</span>
                    </nav>

                    {/* Hero Section */}
                    <div
                        className="min-h-[calc(100vh-200px)] flex flex-col justify-center gap-12 py-20">
                        {/* Main content */}
                        <div className="space-y-6">
                            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-200 via-blue-200 to-purple-200 leading-tight">
                                Your Knowledge,
                                <br/>
                                Beautifully Organized
                            </h1>

                            <p className="text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed">
                                A modern knowledge base built with Docusaurus. Organize your
                                thoughts, save structured information, and access everything with
                                powerful search.
                            </p>

                            {/* CTA Buttons */}
                            <div className="flex flex-col sm:flex-row gap-4 pt-4">
                                <button
                                    className="group relative px-8 py-3 font-semibold overflow-hidden rounded-lg transition-all duration-300">
                                    <div
                                        className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 group-hover:scale-105 transition-transform duration-300"></div>
                                    <div
                                        className="absolute inset-0 backdrop-blur-md bg-white/10"></div>
                                    <span
                                        className="relative text-white flex items-center justify-center gap-2">
                  Start Reading
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform"
                       fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                  </svg>
                </span>
                                </button>

                                <button
                                    className="group px-8 py-3 font-semibold rounded-lg backdrop-blur-md bg-white/10 border border-white/20 hover:bg-white/20 hover:border-white/30 transition-all duration-300 text-white">
                                    Explore Docs
                                </button>
                            </div>
                        </div>

                        {/* Glass cards grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-8">
                            {features.map((feature, idx) => (
                                <div
                                    key={idx}
                                    className="group backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 hover:bg-white/20 hover:border-white/30 transition-all duration-500 hover:shadow-2xl hover:shadow-purple-500/20 cursor-pointer"
                                >
                                    <div className="flex items-start gap-4">
                                        <div
                                            className="p-3 rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20 group-hover:from-purple-500/40 group-hover:to-blue-500/40 transition-colors">
                                            <feature.icon className="w-6 h-6 text-purple-300"/>
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                                            <p className="text-slate-400 text-sm">{feature.description}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Search preview */}
                        <div className="mt-12">
                            <div
                                className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8">
                                <div
                                    className="flex items-center gap-3 bg-white/10 border border-white/20 rounded-xl px-4 py-3 hover:bg-white/20 transition-all duration-300">
                                    <Search className="w-5 h-5 text-slate-400"/>
                                    <input
                                        type="text"
                                        placeholder="Search your knowledge base..."
                                        className="bg-transparent outline-none text-white placeholder-slate-500 w-full"
                                        disabled
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="py-16 grid grid-cols-3 gap-8 text-center">
                        {[
                            {value: '500+', label: 'Topics'},
                            {value: '1000+', label: 'Docs'},
                            {value: '24/7', label: 'Access'}
                        ].map((stat, idx) => (
                            <div key={idx}
                                 className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all">
                                <p className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-blue-300">{stat.value}</p>
                                <p className="text-slate-400 text-sm mt-2">{stat.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer glow */}
                <div
                    className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-500 to-transparent opacity-50"></div>
            </div>
        </Layout>
    );
}