import assert from "node:assert/strict";
import test from "node:test";
import {
  identUrl,
  normalizeVersion,
  sourceUrl,
  srcHref,
  srcLabel,
} from "../src/lib/kernelSource.js";

test("normalizeVersion accepts both v-prefixed and bare versions", () => {
  assert.equal(normalizeVersion("6.18"), "v6.18");
  assert.equal(normalizeVersion("v6.18"), "v6.18");
});

test("sourceUrl points at the Elixir source route", () => {
  assert.equal(
    sourceUrl("v6.18", "fs/namei.c"),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("sourceUrl strips a leading slash from the file path", () => {
  assert.equal(
    sourceUrl("v6.18", "/fs/namei.c"),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("identUrl points at the Elixir identifier route", () => {
  assert.equal(
    identUrl("v6.18", "path_openat"),
    "https://elixir.bootlin.com/linux/v6.18/ident/path_openat",
  );
});

test("srcLabel renders file and symbol together", () => {
  assert.equal(
    srcLabel({ file: "fs/namei.c", symbol: "path_openat" }),
    "fs/namei.c:path_openat()",
  );
});

test("srcLabel renders a bare file and a bare symbol", () => {
  assert.equal(srcLabel({ file: "mm/memory.c" }), "mm/memory.c");
  assert.equal(srcLabel({ symbol: "handle_mm_fault" }), "handle_mm_fault()");
});

test("srcHref prefers the ident route whenever a symbol is given", () => {
  assert.equal(
    srcHref("v6.18", { file: "fs/namei.c", symbol: "path_openat" }),
    "https://elixir.bootlin.com/linux/v6.18/ident/path_openat",
  );
  assert.equal(
    srcHref("v6.18", { file: "fs/namei.c" }),
    "https://elixir.bootlin.com/linux/v6.18/source/fs/namei.c",
  );
});

test("no generated URL ever contains a line number anchor", () => {
  const urls = [
    sourceUrl("v6.18", "fs/namei.c"),
    identUrl("v6.18", "path_openat"),
    srcHref("v6.18", { file: "fs/namei.c", symbol: "path_openat" }),
  ];
  for (const url of urls) {
    assert.ok(!url.includes("#L"), `${url} contains a line anchor`);
  }
});

test("srcLabel throws when given neither a file nor a symbol", () => {
  assert.throws(() => srcLabel({}), /file.*symbol/i);
});
