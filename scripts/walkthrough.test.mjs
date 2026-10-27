import assert from "node:assert/strict";
import test from "node:test";
import { clamp, stepIndexForHash, validate } from "../src/lib/walkthrough.js";

test("clamp keeps an index inside [0, n-1]", () => {
  assert.equal(clamp(-1, 5), 0);
  assert.equal(clamp(0, 5), 0);
  assert.equal(clamp(3, 5), 3);
  assert.equal(clamp(5, 5), 4);
  assert.equal(clamp(99, 1), 0);
});

test("validate rejects a walkthrough with no steps", () => {
  assert.throws(
    () => validate([], "Kruskal"),
    /<Walkthrough "Kruskal"> needs at least one <Step>/,
  );
});

test("validate rejects a step without a title, naming it 1-based", () => {
  assert.throws(
    () => validate([{ title: "Sort" }, { title: "" }], "Kruskal"),
    /<Step> #2 in <Walkthrough "Kruskal"> is missing a title/,
  );
  assert.throws(
    () => validate([{}], undefined),
    /<Step> #1 in <Walkthrough "untitled"> is missing a title/,
  );
});

test("validate accepts well-formed steps", () => {
  assert.doesNotThrow(() => validate([{ title: "A" }, { title: "B" }], "T"));
});

test("stepIndexForHash finds the step containing the target id", () => {
  const contains = [
    (id) => id === "intro",
    () => false,
    () => false,
    (id) => id === "heading in step 4",
  ];
  assert.equal(stepIndexForHash("#intro", contains), 0);
  assert.equal(stepIndexForHash("#heading%20in%20step%204", contains), 3);
});

test("stepIndexForHash returns null for empty or unmatched hashes", () => {
  const contains = [() => false];
  assert.equal(stepIndexForHash("", contains), null);
  assert.equal(stepIndexForHash("#", contains), null);
  assert.equal(stepIndexForHash("#nowhere", contains), null);
});
