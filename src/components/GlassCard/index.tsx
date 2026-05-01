import { cn } from "@lib/utils";
import type { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

export default function GlassCard({ children, className }: GlassCardProps) {
  return (
    <div
      className={cn(
        "relative z-[1] rounded-3xl backdrop-blur-[20px]",
        "border border-purple-500/20 bg-white/70 shadow-[0_8px_32px_rgba(0,0,0,0.06)]",
        "dark:border-white/10 dark:bg-black/40 dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)]",
        className,
      )}
    >
      {children}
    </div>
  );
}
