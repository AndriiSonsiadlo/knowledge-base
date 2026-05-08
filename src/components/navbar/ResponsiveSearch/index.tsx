import clsx from "clsx";
import { Search, X } from "lucide-react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import styles from "./styles.module.css";

const COMPACT_SEARCH_MEDIA = "(max-width: 480px)";
const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

type ResponsiveSearchProps = {
  children: ReactNode;
  className?: string;
};

export default function ResponsiveSearch({
  children,
  className,
}: ResponsiveSearchProps) {
  const [isCompact, setIsCompact] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const modalId = useId();
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const closeModal = useCallback(() => {
    setIsOpen(false);

    if (typeof window !== "undefined") {
      window.requestAnimationFrame(() => {
        triggerRef.current?.focus();
      });
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const media = window.matchMedia(COMPACT_SEARCH_MEDIA);
    const sync = (event?: MediaQueryListEvent) => {
      setIsCompact(event?.matches ?? media.matches);
    };

    sync();
    media.addEventListener("change", sync);

    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!isCompact) {
      setIsOpen(false);
    }
  }, [isCompact]);

  useEffect(() => {
    if (!isOpen || typeof window === "undefined") {
      return;
    }

    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeModal();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const focusable = Array.from(
        panelRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ??
          [],
      );

      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);

    const frame = window.requestAnimationFrame(() => {
      const input = panelRef.current?.querySelector<HTMLElement>(
        "input, button, [tabindex]:not([tabindex='-1'])",
      );
      input?.focus();
    });

    return () => {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      document.removeEventListener("keydown", onKeyDown);
      window.cancelAnimationFrame(frame);
    };
  }, [closeModal, isOpen]);

  if (!isCompact) {
    return (
      <div className={clsx(styles.inlineSearch, className)}>{children}</div>
    );
  }

  const modal =
    isOpen && typeof document !== "undefined"
      ? createPortal(
          <div className={styles.modalBackdrop} aria-hidden={false}>
            <button
              type="button"
              tabIndex={-1}
              className={clsx("clean-btn", styles.backdropDismiss)}
              aria-label="Close search overlay"
              onClick={closeModal}
            />
            <div
              id={modalId}
              ref={panelRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby={`${modalId}-title`}
              className={styles.modalPanel}
            >
              <div className={styles.modalHeader}>
                <p id={`${modalId}-title`} className={styles.modalTitle}>
                  Search the knowledge base
                </p>
                <button
                  type="button"
                  className={clsx("clean-btn", styles.closeButton)}
                  aria-label="Close search"
                  onClick={closeModal}
                >
                  <X size={18} />
                </button>
              </div>
              <div className={styles.modalBody}>{children}</div>
            </div>
          </div>,
          document.body,
        )
      : null;

  return (
    <>
      <div className={clsx(styles.compactSearch, className)}>
        <button
          ref={triggerRef}
          type="button"
          className={clsx("clean-btn", styles.compactTrigger)}
          aria-label="Open search"
          aria-controls={modalId}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
          onClick={() => setIsOpen(true)}
        >
          <Search size={18} />
        </button>
      </div>
      {modal}
    </>
  );
}
