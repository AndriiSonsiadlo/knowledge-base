import PrereqBlock from "@components/PrereqBlock";
import ReadingProgress from "@components/ReadingProgress";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useWindowSize } from "@docusaurus/theme-common";
import ContentVisibility from "@theme/ContentVisibility";
import DocBreadcrumbs from "@theme/DocBreadcrumbs";
import DocItemContent from "@theme/DocItem/Content";
import DocItemFooter from "@theme/DocItem/Footer";
import DocItemPaginator from "@theme/DocItem/Paginator";
import DocItemTOCDesktop from "@theme/DocItem/TOC/Desktop";
import DocItemTOCMobile from "@theme/DocItem/TOC/Mobile";
import DocVersionBadge from "@theme/DocVersionBadge";
import DocVersionBanner from "@theme/DocVersionBanner";
import clsx from "clsx";
import { useEffect, useRef, useState } from "react";
import styles from "./styles.module.css";

/**
 * Decide if the toc should be rendered, on mobile or desktop viewports
 */
function useDocTOC() {
  const { frontMatter, toc } = useDoc();
  const windowSize = useWindowSize();
  const hidden = frontMatter.hide_table_of_contents;
  const canRender = !hidden && toc.length > 0;
  const mobile = canRender ? <DocItemTOCMobile /> : undefined;
  const desktop =
    canRender && (windowSize === "desktop" || windowSize === "ssr") ? (
      <DocItemTOCDesktop />
    ) : undefined;
  return {
    hidden,
    mobile,
    desktop,
  };
}

const dateFormatter = new Intl.DateTimeFormat("en", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

function useReadingTime(articleRef) {
  const [minutes, setMinutes] = useState(null);

  useEffect(() => {
    const node = articleRef.current;
    if (!node) {
      return;
    }
    const words = node.innerText.trim().split(/\s+/).filter(Boolean).length;
    setMinutes(Math.max(1, Math.round(words / 200)));
  }, [articleRef]);

  return minutes;
}

export default function DocItemLayout({ children }) {
  const docTOC = useDocTOC();
  const { metadata } = useDoc();
  const articleRef = useRef(null);
  const readingMinutes = useReadingTime(articleRef);
  return (
    <div className="row">
      <ReadingProgress targetRef={articleRef} />
      <div
        className={clsx("col", "xl:px-10", !docTOC.hidden && styles.docItemCol)}
      >
        <ContentVisibility metadata={metadata} />
        <DocVersionBanner />
        <div className={styles.docItemContainer}>
          <article ref={articleRef}>
            <DocBreadcrumbs />
            {(readingMinutes !== null || metadata.lastUpdatedAt) && (
              <div className={styles.metaRow}>
                {readingMinutes !== null && (
                  <p className={styles.readingTime}>{readingMinutes} min read</p>
                )}
                {metadata.lastUpdatedAt && (
                  <p className={clsx(styles.readingTime, styles.lastUpdated)}>
                    Updated{" "}
                    {dateFormatter.format(new Date(metadata.lastUpdatedAt))}
                  </p>
                )}
              </div>
            )}
            <DocVersionBadge />
            {docTOC.mobile}
            <PrereqBlock variant="before" />
            <DocItemContent>{children}</DocItemContent>
            <PrereqBlock variant="after" />
            <div className={styles.docFooterMetaHidden}>
              <DocItemFooter />
            </div>
          </article>
          <DocItemPaginator />
        </div>
      </div>
      {docTOC.desktop && <div className="col col--3">{docTOC.desktop}</div>}
    </div>
  );
}
