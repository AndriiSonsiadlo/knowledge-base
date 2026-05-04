import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import styles from "./styles.module.css";

export default function CursorGlow(): ReactNode | null {
  const glowRef = useRef<HTMLDivElement>(null);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const coarsePointer = window.matchMedia(
      "(hover: none), (pointer: coarse)",
    ).matches;
    setSupported(!reducedMotion && !coarsePointer);
  }, []);

  useEffect(() => {
    if (!supported) {
      return;
    }

    const parent = glowRef.current?.parentElement;
    if (!parent) {
      return;
    }

    const handleMove = (event: MouseEvent) => {
      const rect = parent.getBoundingClientRect();
      const node = glowRef.current;
      if (!node) {
        return;
      }
      node.style.transform = `translate(${event.clientX - rect.left}px, ${
        event.clientY - rect.top
      }px)`;
      node.classList.add(styles.glowVisible);
    };

    const handleLeave = () => {
      glowRef.current?.classList.remove(styles.glowVisible);
    };

    parent.addEventListener("mousemove", handleMove);
    parent.addEventListener("mouseleave", handleLeave);
    return () => {
      parent.removeEventListener("mousemove", handleMove);
      parent.removeEventListener("mouseleave", handleLeave);
    };
  }, [supported]);

  if (!supported) {
    return null;
  }

  return <div ref={glowRef} className={styles.glow} />;
}
