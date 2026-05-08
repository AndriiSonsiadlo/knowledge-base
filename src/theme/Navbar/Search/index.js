import ResponsiveSearch from "@components/navbar/ResponsiveSearch";
import clsx from "clsx";
import styles from "./styles.module.css";

export default function NavbarSearch({ children, className }) {
  return (
    <ResponsiveSearch className={clsx(className, styles.navbarSearchContainer)}>
      {children}
    </ResponsiveSearch>
  );
}
