import React from "react";
import clsx from "clsx";
import ResponsiveSearch from "@components/navbar/ResponsiveSearch";
import styles from "./styles.module.css";

export default function NavbarSearch({ children, className }) {
  return (
    <ResponsiveSearch className={clsx(className, styles.navbarSearchContainer)}>
      {children}
    </ResponsiveSearch>
  );
}
