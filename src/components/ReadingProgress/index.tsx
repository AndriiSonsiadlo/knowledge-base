import type { ReactNode, RefObject } from "react";
import { useEffect, useState } from "react";
import styles from "./styles.module.css";

interface ReadingProgressProps {
  targetRef: RefObject<HTMLElement | null>;
}

export default function ReadingProgress({
  targetRef,
}: ReadingProgressProps): ReactNode {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const node = targetRef.current;
      if (!node) {
        return;
      }
      const rect = node.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      if (total <= 0) {
        setProgress(100);
        return;
      }
      const scrolled = Math.min(Math.max(-rect.top, 0), total);
      setProgress((scrolled / total) * 100);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  }, [targetRef]);

  return (
    <div className={styles.progressTrack}>
      <div className={styles.progressFill} style={{ width: `${progress}%` }} />
    </div>
  );
}
