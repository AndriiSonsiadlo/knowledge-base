import NavbarContent from "@theme/Navbar/Content";
import NavbarLayout from "@theme/Navbar/Layout";
import React, { type ReactNode } from "react";

export default function Navbar(): ReactNode {
  return (
    <NavbarLayout>
      <NavbarContent />
    </NavbarLayout>
  );
}
