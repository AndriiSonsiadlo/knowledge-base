import React, {type ComponentProps, type ReactNode, useState} from 'react';
import clsx from 'clsx';
import {useThemeConfig, useColorMode} from '@docusaurus/theme-common';
import {
    useHideableNavbar,
    useNavbarMobileSidebar,
} from '@docusaurus/theme-common/internal';
import {translate} from '@docusaurus/Translate';
import NavbarMobileSidebar from '@theme/Navbar/MobileSidebar';
import type {Props} from '@theme/Navbar/Layout';
import { Menu, X, Search, Moon, Sun } from 'lucide-react';

import styles from './styles.module.css';

function NavbarBackdrop(props: ComponentProps<'div'>) {
    return (
        <div
            role="presentation"
            {...props}
            className={clsx('navbar-sidebar__backdrop', props.className)}
        />
    );
}

export default function NavbarLayout({children}: Props): ReactNode {
    const [isOpen, setIsOpen] = useState(false);
    const {
        navbar: {hideOnScroll},
    } = useThemeConfig();
    const { colorMode, setColorMode } = useColorMode();
    const isDarkTheme = colorMode === 'dark';
    const mobileSidebar = useNavbarMobileSidebar();
    const {navbarRef, isNavbarVisible} = useHideableNavbar(hideOnScroll);

    const toggleTheme = () => {
        setColorMode(isDarkTheme ? 'light' : 'dark');
    };

    return (
        <nav
            ref={navbarRef}
            aria-label={translate({
                id: 'theme.NavBar.navAriaLabel',
                message: 'Main',
                description: 'The ARIA label for the main navigation',
            })}
            className={clsx(
                'sticky top-0 z-50 backdrop-blur-xl transition-colors duration-300',
                isDarkTheme
                    ? 'bg-slate-900/50 border-b border-white/10'
                    : 'bg-white/80 border-b border-slate-200',
                hideOnScroll && [
                    styles.navbarHideable,
                    !isNavbarVisible && styles.navbarHidden,
                ],
                {
                    'navbar-sidebar--show': mobileSidebar.shown,
                },
            )}>

            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">

                    {/* Logo */}
                    <div className="flex items-center gap-3 group cursor-pointer">
                        <div className={clsx(
                            'p-2 rounded-lg transition-colors',
                            isDarkTheme
                                ? 'bg-gradient-to-br from-purple-500/20 to-blue-500/20 group-hover:from-purple-500/40 group-hover:to-blue-500/40'
                                : 'bg-gradient-to-br from-purple-500/10 to-blue-500/10 group-hover:from-purple-500/20 group-hover:to-blue-500/20'
                        )}>
                            <svg className={clsx(
                                'w-6 h-6',
                                isDarkTheme ? 'text-purple-300' : 'text-purple-600'
                            )} fill="currentColor" viewBox="0 0 24 24">
                                <path d="M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z" />
                            </svg>
                        </div>
                        <span className={clsx(
                            'text-lg font-bold transition-colors',
                            isDarkTheme ? 'text-white' : 'text-slate-900'
                        )}>Knowledge Base</span>
                    </div>

                    {/* Desktop Nav */}
                    <div className="hidden md:flex items-center gap-8">
                        {children}
                    </div>

                    {/* Search & Mobile Menu */}
                    <div className="flex items-center gap-4">
                        <div className={clsx(
                            'hidden sm:flex items-center gap-2 backdrop-blur-md rounded-lg px-3 py-2 transition-all',
                            isDarkTheme
                                ? 'bg-white/5 border border-white/10 hover:bg-white/10'
                                : 'bg-slate-100/50 border border-slate-300 hover:bg-slate-100'
                        )}>
                            <Search className={clsx(
                                'w-4 h-4',
                                isDarkTheme ? 'text-slate-400' : 'text-slate-500'
                            )} />
                            <input
                                type="text"
                                placeholder="Search..."
                                className={clsx(
                                    'bg-transparent outline-none text-sm w-32 placeholder-opacity-50 transition-colors',
                                    isDarkTheme
                                        ? 'text-white placeholder-slate-500'
                                        : 'text-slate-900 placeholder-slate-400'
                                )}
                            />
                        </div>

                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className={clsx(
                                'hidden sm:flex p-2 rounded-lg transition-all duration-300',
                                isDarkTheme
                                    ? 'hover:bg-white/10 text-slate-400 hover:text-white'
                                    : 'hover:bg-slate-200 text-slate-600 hover:text-slate-900'
                            )}
                            aria-label="Toggle theme"
                        >
                            {isDarkTheme ? (
                                <Sun className="w-5 h-5" />
                            ) : (
                                <Moon className="w-5 h-5" />
                            )}
                        </button>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className={clsx(
                                'md:hidden p-2 rounded-lg transition-colors',
                                isDarkTheme
                                    ? 'hover:bg-white/10 text-white'
                                    : 'hover:bg-slate-200 text-slate-900'
                            )}
                        >
                            {isOpen ? (
                                <X className="w-6 h-6" />
                            ) : (
                                <Menu className="w-6 h-6" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Mobile Nav */}
                {isOpen && (
                    <div className={clsx(
                        'md:hidden border-t py-4 space-y-2 backdrop-blur-xl',
                        isDarkTheme
                            ? 'border-white/10'
                            : 'border-slate-200'
                    )}>
                        {children}
                    </div>
                )}
            </div>

            <NavbarBackdrop onClick={mobileSidebar.toggle} />
            <NavbarMobileSidebar />
        </nav>
    );
}