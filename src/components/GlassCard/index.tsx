import type { ReactNode } from "react";
import { cn } from "@lib/utils";

interface GlassCardProps {
	children: ReactNode;
	className?: string;
	hover?: boolean;
}

export default function GlassCard({
	children,
	className,
	hover = false,
}: GlassCardProps) {
	return (
		<div
			className={cn(
				"relative z-[1] rounded-3xl backdrop-blur-xl",
				"border border-purple-500/20 bg-white/70 shadow-[0_8px_32px_rgba(0,0,0,0.06)]",
				"dark:border-white/10 dark:bg-black/40 dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)]",
				hover &&
					"transition-all duration-300 hover:border-white/30 hover:bg-white/10",
				className,
			)}
		>
			{children}
		</div>
	);
}
