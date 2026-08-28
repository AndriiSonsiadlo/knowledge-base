import { useDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import BackToTopButton from "@theme/BackToTopButton";
import DocRootLayoutMain from "@theme/DocRoot/Layout/Main";
import DocRootLayoutSidebar from "@theme/DocRoot/Layout/Sidebar";
import { useEffect, useRef, useState } from "react";
import styles from "./styles.module.css";

const SIDEBAR_COLLAPSED_KEY = "docs-sidebar-collapsed";

function readStoredCollapsed() {
  try {
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

export default function DocRootLayout({ children }) {
  const sidebar = useDocsSidebar();
  const [hiddenSidebarContainer, setHiddenSidebarContainer] = useState(false);
  const skipNextWrite = useRef(true);

  // Read the stored preference after mount rather than in the initializer,
  // so the SSR/first-hydration render stays `false` on both sides.
  useEffect(() => {
    if (readStoredCollapsed()) {
      setHiddenSidebarContainer(true);
    }
  }, []);

  useEffect(() => {
    if (skipNextWrite.current) {
      skipNextWrite.current = false;
      return;
    }
    try {
      localStorage.setItem(
        SIDEBAR_COLLAPSED_KEY,
        String(hiddenSidebarContainer),
      );
    } catch {
      // ignore (private browsing, storage disabled, etc.)
    }
  }, [hiddenSidebarContainer]);

  return (
    <div className={styles.docsWrapper}>
      <BackToTopButton />
      <div className={styles.docRoot}>
        {sidebar && (
          <DocRootLayoutSidebar
            sidebar={sidebar.items}
            hiddenSidebarContainer={hiddenSidebarContainer}
            setHiddenSidebarContainer={setHiddenSidebarContainer}
          />
        )}
        <DocRootLayoutMain hiddenSidebarContainer={hiddenSidebarContainer}>
          {children}
        </DocRootLayoutMain>
      </div>
    </div>
  );
}
