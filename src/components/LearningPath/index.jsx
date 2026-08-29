import Link from "@docusaurus/Link";

// <LearningPath /> — one curated route through the section.
//
// The section's dependency graph is validated at build time by
// knowledge-graph-plugin and surfaced per page by <PrereqBlock>. What a reader
// actually needs on the roadmap is not a picture of 229 nodes but an ordered
// route they can click through, so that is what this renders: numbered chips,
// in reading order, each one a real link.
//
// Steps are written by hand in the page, not derived from the graph. That is
// deliberate — a learning path is an editorial choice about what to read next,
// which is a different thing from what a page technically depends on.
//
// Usage in markdown:
//   <LearningPath
//     title="I just want to understand my machine"
//     steps={[
//       ["The kernel/user-space boundary", "./the-kernel-userspace-boundary.md"],
//       ["What Linux actually is", "./what-linux-actually-is.md"],
//     ]} />

// Docusaurus's remark link-resolution transform (mdx-loader's
// resolveMarkdownLinks) only walks real markdown `[text](url)` AST nodes —
// it never sees strings buried inside a JSX prop like `steps`. Left alone,
// `<Link to="./x.md">` here would render that ".md" straight into the href
// and fail the build's broken-link check. So this does by hand what that
// transform does for markdown links: drop the extension, and strip a
// leading `NN-` from every path segment the same way the default
// numberPrefixParser does when computing a doc's real id/URL (see
// @docusaurus/plugin-content-docs's numberPrefix.js) — folder names like
// `04-kernel-architecture-and-idioms` keep their prefix on disk but not in
// the URL.
const NUMBER_PREFIX = /^(\d+)\s*[-_.]+\s*(?=[^-_.\s])/;
const IGNORED_NUMBER_PREFIX = /^\d+[-_.]\d+/; // dates/versions, e.g. "7.0-foo"

function toRoute(relativePath) {
  return relativePath
    .replace(/\.mdx?$/, "")
    .split("/")
    .map((segment) =>
      IGNORED_NUMBER_PREFIX.test(segment)
        ? segment
        : segment.replace(NUMBER_PREFIX, ""),
    )
    .join("/");
}

export default function LearningPath({ title, steps = [] }) {
  if (!title) {
    throw new Error("<LearningPath> requires a `title`");
  }
  return (
    <section className="kb-path">
      <h3 className="kb-path__title">{title}</h3>
      <ol className="kb-path__list">
        {steps.map(([label, href], index) => (
          <li className="kb-path__item" key={href}>
            <Link className="kb-path__link" to={toRoute(href)}>
              <span className="kb-path__index">{index + 1}</span>
              {label}
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
