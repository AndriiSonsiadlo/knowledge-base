import React, { ReactNode } from 'react';
import CategoryCard from '../CategoryCard';
import styles from './styles.module.css';

interface Category {
    title: string;
    description: string;
    icon: string;
    href: string;
    color: 'purple' | 'blue' | 'cyan' | 'green' | 'pink';
}

const categories: Category[] = [
    {
        title: 'Programming',
        description: 'Learn Python, C++, and master modern programming languages with practical examples.',
        icon: '💻',
        href: '/docs/programming/intro',
        color: 'purple',
    },
    {
        title: 'Computer Science',
        description: 'Deep dive into OS, architecture, memory management, and processor design.',
        icon: '⚙️',
        href: '/docs/computer-science/intro',
        color: 'blue',
    },
    {
        title: 'Data & Algorithms',
        description: 'Explore sorting, searching, and fundamental algorithm design patterns.',
        icon: '📊',
        href: '/docs/data-structures-algorithms/intro',
        color: 'cyan',
    },
    {
        title: 'Machine Learning',
        description: 'Master fundamentals, neural networks, NLP, and modern ML architectures.',
        icon: '🤖',
        href: '/docs/machine-learning/intro',
        color: 'green',
    },
];

export default function CategoryGrid(): ReactNode {
    return (
        <section className={styles.categoryGrid}>
            <div className="container">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold mb-4 text-slate-100 drop-shadow-lg">
                        Knowledge Categories
                    </h2>
                    <p className="text-lg text-slate-200 drop-shadow mx-auto">
                        Explore comprehensive guides and structured learning paths across computer science, programming, and AI.
                    </p>
                </div>

                <div className={styles.grid}>
                    {categories.map((category, idx) => (
                        <CategoryCard
                            key={idx}
                            {...category}
                        />
                    ))}
                </div>
            </div>
        </section>
    );
}
