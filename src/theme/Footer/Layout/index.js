import clsx from "clsx";
import styles from "./styles.module.css";

export default function FooterLayout({ style, links, logo, copyright }) {
  return (
    <footer className={clsx(styles.footer)}>
      <div className="mx-auto max-w-7xl px-4 py-6">
        {links}
        {(logo || copyright) && (
          <div className="footer__bottom text--center">
            {logo && <div className="margin-bottom--sm">{logo}</div>}
            {copyright}
          </div>
        )}
      </div>
    </footer>
  );
}
