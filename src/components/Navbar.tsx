import React, {JSX} from 'react';
import { Menu, X, Search } from 'lucide-react';
import { useState } from 'react';

export default function Navbar(): JSX.Element {
    const [isOpen, setIsOpen] = useState(false);

    const navLinks = [
        { label: 'Docs', href: '/docs' },
        { label: 'Guides', href: '/docs/guides' },
        { label: 'Reference', href: '/docs/reference' },
    ];

    return (
        <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/50 border-b border-white/10">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center gap-3 group cursor-pointer">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20 group-hover:from-purple-500/40 group-hover:to-blue-500/40 transition-colors">
                            <svg className="w-6 h-6 text-purple-300" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z" />
                            </svg>
                        </div>
                        <span className="text-lg font-bold text-white">Knowledge Base</span>
                    </div>

                    {/* Desktop Nav */}
                    <div className="hidden md:flex items-center gap-8">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="text-slate-300 hover:text-white transition-colors relative group"
                            >
                                {link.label}
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-400 to-blue-400 group-hover:w-full transition-all duration-300"></span>
                            </a>
                        ))}
                    </div>

                    {/* Search & Mobile Menu */}
                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex items-center gap-2 backdrop-blur-md bg-white/5 border border-white/10 rounded-lg px-3 py-2 hover:bg-white/10 transition-all">
                            <Search className="w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                placeholder="Search..."
                                className="bg-transparent outline-none text-sm text-white placeholder-slate-500 w-32"
                            />
                        </div>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            {isOpen ? (
                                <X className="w-6 h-6 text-white" />
                            ) : (
                                <Menu className="w-6 h-6 text-white" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Mobile Nav */}
                {isOpen && (
                    <div className="md:hidden border-t border-white/10 py-4 space-y-2 backdrop-blur-xl">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="block px-4 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                            >
                                {link.label}
                            </a>
                        ))}
                    </div>
                )}
            </div>
        </nav>
    );
}
