import assert from "node:assert/strict";
import test from "node:test";
import remarkWavedrom from "../src/plugins/remark-wavedrom.js";

// Runs the transformer over a one-node tree and returns the transformed node.
// `file.fail` is how remark reports a fatal error; we make it throw so tests can catch it.
function transform(node) {
  const tree = { type: "root", children: [node] };
  const file = {
    fail(message) {
      throw new Error(message);
    },
  };
  remarkWavedrom()(tree, file);
  return tree.children[0];
}

function fence(value, meta) {
  return { type: "code", lang: "wavedrom", meta, value };
}

const WAVE = "{ signal: [{name: 'clk', wave: 'p...'}] }";
const REG = "{ reg: [{bits: 2, name: 'MODE'}, {bits: 30, name: 'rest'}] }";

test("renders a signal fence to an mdxJsxFlowElement", () => {
  const out = transform(fence(WAVE, 'alt="clock"'));
  assert.equal(out.type, "mdxJsxFlowElement");
  assert.equal(out.name, "WaveDrom");
  const svg = out.attributes.find((a) => a.name === "svg");
  assert.ok(svg.value.startsWith("<svg"));
  assert.ok(svg.value.includes("</svg>"));
});

test("renders a reg fence to a bit-field diagram", () => {
  const out = transform(fence(REG, 'alt="MODE field"'));
  const svg = out.attributes.find((a) => a.name === "svg");
  assert.ok(svg.value.startsWith("<svg"));
  assert.ok(svg.value.includes("MODE"));
});

// The regression guard. A raw `html` node would make MDX parse WaveDrom's
// embedded <style> block as JSX and fail the build.
test("never emits a raw html node", () => {
  const out = transform(fence(WAVE, 'alt="clock"'));
  assert.notEqual(out.type, "html");
});

test("passes title through as a caption and alt as alt", () => {
  const out = transform(fence(WAVE, 'title="SPI mode 0" alt="SPI mode 0 timing"'));
  const attr = (n) => out.attributes.find((a) => a.name === n)?.value;
  assert.equal(attr("caption"), "SPI mode 0");
  assert.equal(attr("alt"), "SPI mode 0 timing");
});

test("falls back to title when alt is absent", () => {
  const out = transform(fence(WAVE, 'title="SPI mode 0"'));
  const attr = (n) => out.attributes.find((a) => a.name === n)?.value;
  assert.equal(attr("alt"), "SPI mode 0");
});

test("fails the build when neither alt nor title is given", () => {
  assert.throws(() => transform(fence(WAVE, undefined)), /alt=|title=/);
});

test("fails the build on unparseable source", () => {
  assert.throws(() => transform(fence("{ signal: [", 'alt="x"')), /JSON5|parse/i);
});

test("leaves other code fences untouched", () => {
  const node = { type: "code", lang: "c", value: "int main(void) { return 0; }" };
  const out = transform(node);
  assert.equal(out.type, "code");
  assert.equal(out.lang, "c");
});
