// Pure step logic for <Walkthrough />, kept free of React and the DOM so it can
// be unit-tested with node --test (scripts/walkthrough.test.mjs).

// Keeps a step index inside [0, n-1]. Navigation never wraps around.
export function clamp(i, n) {
  return Math.max(0, Math.min(i, n - 1));
}

// Throws on a malformed walkthrough. Called during render, so during the static
// build a bad page fails `npm run build` with the route in the error output.
// `steps` is a list of Step props ({ title, ... }).
export function validate(steps, title) {
  const name = title || "untitled";
  if (steps.length === 0) {
    throw new Error(`<Walkthrough "${name}"> needs at least one <Step>`);
  }
  steps.forEach((step, i) => {
    if (typeof step.title !== "string" || step.title.trim() === "") {
      throw new Error(
        `<Step> #${i + 1} in <Walkthrough "${name}"> is missing a title`,
      );
    }
  });
}

// Which step holds the element a URL hash points at? `contains[i](id)` answers
// "is #id inside step i". Returns the first matching index, or null.
export function stepIndexForHash(hash, contains) {
  const raw = (hash || "").replace(/^#/, "");
  if (!raw) return null;
  let id;
  try {
    id = decodeURIComponent(raw);
  } catch {
    id = raw;
  }
  const i = contains.findIndex((has) => has(id));
  return i === -1 ? null : i;
}
