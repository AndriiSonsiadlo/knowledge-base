import { cn } from "@lib/utils";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

export default function BackToTop(): ReactNode {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > 600);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <button
      type="button"
      aria-label="Back to top"
      className={cn(styles.button, visible && styles.buttonVisible)}
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
    >
      <span className={styles.icon} />
    </button>
  );
}
