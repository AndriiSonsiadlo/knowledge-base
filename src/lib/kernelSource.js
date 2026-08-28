// Builds elixir.bootlin.com URLs for the pinned kernel version.
//
// Deliberately line-number-free: line numbers rot within one release, while
// file paths and symbol names survive for years. Elixir's `ident/` route
// resolves a symbol to its definition and all its uses with no line number,
// which is why it is preferred whenever a symbol is known.
//
// The version itself lives in one place only — `customFields.linuxKernelVersion`
// in docusaurus.config.js — so re-pinning the section is a one-line change.

const ELIXIR_BASE = "https://elixir.bootlin.com/linux";

export function normalizeVersion(version) {
  const trimmed = String(version).trim();
  return trimmed.startsWith("v") ? trimmed : `v${trimmed}`;
}

export function sourceUrl(version, file) {
  const path = String(file).replace(/^\/+/, "");
  return `${ELIXIR_BASE}/${normalizeVersion(version)}/source/${path}`;
}

export function identUrl(version, symbol) {
  return `${ELIXIR_BASE}/${normalizeVersion(version)}/ident/${symbol}`;
}

export function srcLabel({ file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  if (file && symbol) return `${file}:${symbol}()`;
  if (file) return file;
  return `${symbol}()`;
}

export function srcHref(version, { file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  return symbol ? identUrl(version, symbol) : sourceUrl(version, file);
}
