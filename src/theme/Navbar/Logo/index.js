import Link from "@docusaurus/Link";

// Workbench brand: a prompt glyph and the repo name, set in the mono face.
export default function NavbarLogo() {
  return (
    <Link
      to="/"
      className="navbar__brand wb-brand"
      aria-label="knowledge-base home"
    >
      <span className="wb-brand__mark" aria-hidden="true">
        &gt;_
      </span>
      <span>knowledge-base</span>
    </Link>
  );
}
