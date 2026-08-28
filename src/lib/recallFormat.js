import katex from "katex";

// Recall props are plain JS strings (MDX component attributes, not markdown),
// so remark-math/rehype-katex never see them. This does the same job for that
// one narrow case: backtick spans become inline code, and O(...)/Θ(...)/Ω(...)/
// o(...)/ω(...) expressions become KaTeX, without requiring $-delimiters authors
// would have to remember only inside <Recall> props.

const SUPER = {
  "⁰": "0",
  "¹": "1",
  "²": "2",
  "³": "3",
  "⁴": "4",
  "⁵": "5",
  "⁶": "6",
  "⁷": "7",
  "⁸": "8",
  "⁹": "9",
  ⁿ: "n",
};
const SUB = { "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5" };
const GREEK = {
  Θ: "\\Theta",
  Ω: "\\Omega",
  α: "\\alpha",
  φ: "\\varphi",
  ω: "\\omega",
};

function toLatex(expr) {
  let out = expr;
  // literal "^(...)" and "^token" exponents need explicit braces, or KaTeX
  // only raises the first character.
  out = out.replace(/\^\(([^()]*)\)/g, "^{$1}");
  out = out.replace(/\^([^\s(){}]+)/g, "^{$1}");
  out = out.replace(
    /[⁰¹²³⁴⁵⁶⁷⁸⁹ⁿ]+/g,
    (run) => `^{${[...run].map((c) => SUPER[c]).join("")}}`,
  );
  out = out.replace(
    /[₀₁₂₃₄₅]+/g,
    (run) => `_{${[...run].map((c) => SUB[c]).join("")}}`,
  );
  out = out.replace(/\blog(_\{[^}]*\}|_\w)?/g, (_, sub) => `\\log${sub ?? ""}`);
  for (const [glyph, latex] of Object.entries(GREEK))
    out = out.split(glyph).join(latex);
  out = out.replaceAll("·", " \\cdot ").replaceAll("−", "-");
  return out;
}

function renderMath(latex) {
  try {
    return katex.renderToString(latex, { throwOnError: false, output: "html" });
  } catch {
    return latex;
  }
}

const escapeHtml = (s) =>
  s.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );

// `code` spans, *italic*/**bold** emphasis, or a bare O(...)/Θ(...)/Ω(...)/
// o(...)/ω(...) expression not preceded by a letter (so "also(x)" doesn't
// get read as little-o notation). Order matters: ** before * so bold wins.
const TOKEN_RE =
  /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*|(?<![A-Za-z])([oOΘΩω])(\((?:[^()]|\([^()]*\))*\))/g;

export function formatRecallText(text) {
  if (!text) return "";
  let html = "";
  let last = 0;
  for (const match of text.matchAll(TOKEN_RE)) {
    html += escapeHtml(text.slice(last, match.index));
    const [full, code, bold, italic, prefix, parens] = match;
    if (code !== undefined) {
      html += `<code>${escapeHtml(code)}</code>`;
    } else if (bold !== undefined) {
      html += `<strong>${escapeHtml(bold)}</strong>`;
    } else if (italic !== undefined) {
      html += `<em>${escapeHtml(italic)}</em>`;
    } else {
      const inner = parens.slice(1, -1);
      const latexPrefix = GREEK[prefix] ?? prefix;
      html += renderMath(`${latexPrefix}(${toLatex(inner)})`);
    }
    last = match.index + full.length;
  }
  html += escapeHtml(text.slice(last));
  return html;
}
