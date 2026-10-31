// Prism theme for the Workbench design (mockups/ide palette). Colours are
// CSS variables defined per theme in src/css/workbench.css, so one object
// serves both light and dark mode.

/** @type {import('prism-react-renderer').PrismTheme} */
const workbenchPrismTheme = {
  plain: { color: "var(--wb-code-ink)", backgroundColor: "var(--wb-code-bg)" },
  styles: [
    {
      types: ["comment", "prolog", "doctype", "cdata"],
      style: { color: "var(--wb-syn-comment)", fontStyle: "italic" },
    },
    {
      types: ["punctuation", "operator"],
      style: { color: "var(--wb-syn-punct)" },
    },
    {
      types: ["keyword", "atrule", "important", "selector", "rule"],
      style: { color: "var(--wb-syn-keyword)" },
    },
    {
      types: ["class-name", "builtin", "namespace", "tag", "symbol"],
      style: { color: "var(--wb-syn-type)" },
    },
    {
      types: ["function", "function-variable", "macro", "directive"],
      style: { color: "var(--wb-syn-fn)" },
    },
    {
      types: ["string", "char", "attr-value", "regex", "url", "inserted"],
      style: { color: "var(--wb-syn-string)" },
    },
    {
      types: ["number", "boolean", "constant", "attr-name", "property"],
      style: { color: "var(--wb-syn-number)" },
    },
    { types: ["deleted"], style: { color: "var(--wb-danger-ink)" } },
    {
      types: ["variable", "parameter"],
      style: { color: "var(--wb-code-ink)" },
    },
    { types: ["bold"], style: { fontWeight: "bold" } },
    { types: ["italic"], style: { fontStyle: "italic" } },
  ],
};

export default workbenchPrismTheme;
