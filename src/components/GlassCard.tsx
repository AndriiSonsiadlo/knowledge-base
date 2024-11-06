import React, {JSX} from 'react';

interface GlassCardProps {
    title: string;
    description?: string;
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export default function GlassCard({
                                      title,
                                      description,
                                      children,
                                      className = '',
                                      hover = true,
                                  }: GlassCardProps): JSX.Element {
    return (
        <div
            className={`backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 ${
                hover ? 'hover:bg-white/10 hover:border-white/30 transition-all duration-300' : ''
            } ${className}`}
        >
            {(title || description) && (
                <div className="mb-4">
                    {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
                    {description && <p className="text-sm text-slate-400 mt-1">{description}</p>}
                </div>
            )}
            {children}
        </div>
    );
}
