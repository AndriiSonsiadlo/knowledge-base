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

// SCREAMING_SNAKE_CASE symbols are config options and macro constants
// (CONFIG_*, VM_FAULT_*, ...) — never called with `()`.
const ALL_CAPS = /^[A-Z_][A-Z0-9_]*$/;

// Typedef names conventionally end in `_t` and, like the constants above,
// are never called.
const TYPEDEF_SUFFIX = /_t$/;

// Struct tags and plain global variables cited by <Src symbol="..."> that
// aren't otherwise distinguishable from a function name by spelling alone
// (a struct tag like `sk_buff` and a function like `do_exit` are both
// ordinary lower_snake_case identifiers). Extend this set rather than
// touching call sites when a new non-callable symbol is cited.
const KNOWN_NON_FUNCTIONS = new Set([
  "sk_buff",
  "setup_header",
  "new_utsname",
  "nsproxy",
  "e820_table",
  "saved_command_line",
  "ovl_fs_type",
]);

function isCallable(symbol) {
  if (ALL_CAPS.test(symbol)) return false;
  if (TYPEDEF_SUFFIX.test(symbol)) return false;
  if (KNOWN_NON_FUNCTIONS.has(symbol)) return false;
  return true;
}

export function srcLabel({ file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  const symbolLabel = symbol && isCallable(symbol) ? `${symbol}()` : symbol;
  if (file && symbol) return `${file}:${symbolLabel}`;
  if (file) return file;
  return symbolLabel;
}

export function srcHref(version, { file, symbol }) {
  if (!file && !symbol) {
    throw new Error("<Src> needs at least one of `file` or `symbol`");
  }
  return symbol ? identUrl(version, symbol) : sourceUrl(version, file);
}
