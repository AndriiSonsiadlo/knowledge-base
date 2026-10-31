import { clamp, stepIndexForHash, validate } from "@site/src/lib/walkthrough";
import { Children, cloneElement, useEffect, useRef, useState } from "react";

// <Walkthrough /> — a worked example shown one step at a time.
//
// Every step is always in the HTML, so readers without JS, print, and site
// search get all of them. Inactive steps are hidden only under html[data-kb-js] (a
// head script in docusaurus.config.js adds it before first paint).
//
// Usage in markdown (global MDX components, no import; blank lines around step
// content are required, same as <TabItem>):
//   <Walkthrough title="Kruskal on five vertices" accent="blue">
//     <Step title="Sort the edges">
//
//   Sorted: `(A,B,1) (B,C,2) …`
//
//     </Step>
//     <Step title="Take A–B">
//
//   Union-find merges them into <StepChange>`{A,B}`</StepChange>.
//
//     </Step>
//   </Walkthrough>

export function Step({ title, _index, _active, _hidden, children }) {
  return (
    <div
      className={`kb-wt__panel${_active ? " is-active" : ""}`}
      aria-hidden={_hidden || undefined}
      inert={_hidden || undefined}
    >
      <div className="kb-wt__step-title">
        <span className="kb-wt__step-num">Step {_index + 1}</span>
        <span>{title}</span>
      </div>
      <div className="kb-wt__body">{children}</div>
    </div>
  );
}

export function StepChange({ label = "changed", children }) {
  return (
    <span className="kb-wt-change">
      {children}
      <span className="kb-wt-change__badge">{label}</span>
    </span>
  );
}

export function Walkthrough({
  title,
  caption,
  accent = "green",
  fixedHeight = true,
  children,
}) {
  const all = Children.toArray(children);
  const steps = all.filter((c) => c?.type === Step);
  validate(
    steps.map((s) => s.props),
    title,
  );
  if (process.env.NODE_ENV !== "production") {
    const stray = all.filter(
      (c) => c?.type !== Step && !(typeof c === "string" && !c.trim()),
    );
    if (stray.length) {
      console.warn(
        `<Walkthrough "${title || "untitled"}"> ignores ${stray.length} non-<Step> child(ren)`,
      );
    }
  }

  const n = steps.length;
  const [current, setCurrent] = useState(0);
  const [mounted, setMounted] = useState(false);
  const [announce, setAnnounce] = useState("");
  const rootRef = useRef(null);
  const prevRef = useRef(null);
  const nextRef = useRef(null);

  // Deep links: a hash pointing inside a hidden step activates that step.
  useEffect(() => {
    setMounted(true);
    const root = rootRef.current;
    if (!root) return undefined;
    const panels = [
      ...root.querySelectorAll(":scope > .kb-wt__panels > .kb-wt__panel"),
    ];
    const contains = panels.map(
      (p) => (id) => !!p.querySelector(`#${CSS.escape(id)}`),
    );
    const sync = () => {
      const i = stepIndexForHash(window.location.hash, contains);
      if (i === null) return;
      setCurrent(i);
      const id = decodeURIComponent(window.location.hash.slice(1));
      requestAnimationFrame(() =>
        document.getElementById(id)?.scrollIntoView(),
      );
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const go = (i) => {
    const next = clamp(i, n);
    setCurrent(next);
    setAnnounce(`Step ${next + 1} of ${n}: ${steps[next].props.title}`);
    // Never leave focus on a button that just became disabled.
    const active = document.activeElement;
    if (next === n - 1 && active === nextRef.current) prevRef.current?.focus();
    if (next === 0 && active === prevRef.current) nextRef.current?.focus();
  };

  const onKeyDown = (e) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      go(current + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      go(current - 1);
    }
  };

  if (n === 1) {
    return <div className="kb-wt__single">{steps[0].props.children}</div>;
  }

  return (
    <section
      ref={rootRef}
      className={`kb-wt${fixedHeight ? "" : " kb-wt--auto-height"}`}
      data-accent={accent}
      aria-roledescription="walkthrough"
      aria-label={title}
    >
      {title && <div className="kb-wt__title">{title}</div>}
      <div className="kb-wt__panels">
        {steps.map((s, i) =>
          cloneElement(s, {
            key: s.key ?? i,
            _index: i,
            _active: i === current,
            _hidden: mounted && i !== current,
          }),
        )}
      </div>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: arrow keys while focus is on the buttons inside */}
      <div className="kb-wt__controls" onKeyDown={onKeyDown}>
        <ol className="kb-wt__rail">
          {steps.map((s, i) => (
            <li key={s.key ?? i}>
              <button
                type="button"
                className={`kb-wt__dot${i === current ? " is-active" : ""}`}
                aria-label={`Step ${i + 1}: ${s.props.title}`}
                aria-current={i === current ? "step" : undefined}
                onClick={() => go(i)}
              >
                {i + 1}
              </button>
            </li>
          ))}
        </ol>
        <div className="kb-wt__nav">
          <button
            ref={prevRef}
            type="button"
            className="kb-wt__btn"
            disabled={current === 0}
            onClick={() => go(current - 1)}
          >
            ← Previous
          </button>
          <span className="kb-wt__counter">
            Step {current + 1} of {n}
          </span>
          <button
            ref={nextRef}
            type="button"
            className="kb-wt__btn"
            disabled={current === n - 1}
            onClick={() => go(current + 1)}
          >
            Next →
          </button>
        </div>
      </div>
      <div className="kb-wt__live" aria-live="polite">
        {announce}
      </div>
      {caption && <div className="kb-wt__caption">{caption}</div>}
    </section>
  );
}
