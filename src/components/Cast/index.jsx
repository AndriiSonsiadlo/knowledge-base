import useBaseUrl from "@docusaurus/useBaseUrl";
import { useEffect, useRef } from "react";
import "asciinema-player/dist/bundle/asciinema-player.css";

// <Cast /> — a replayable terminal session.
//
// The player library touches `document` at import time, so it is imported
// dynamically inside an effect. Effects never run during server rendering,
// which makes this SSR-safe without a <BrowserOnly> wrapper — the wrapper
// would add a component boundary and change nothing about the guarantee.
// The stylesheet is a static import because CSS is safe to import at module
// scope and webpack extracts it at build time.
//
// Every cast on a page is accompanied by the decisive output as a plain text
// code block: casts are not indexed by the offline search, do not render
// without JavaScript, and cannot be copied from. The text block is the
// content; the cast shows the interaction.
//
// Usage in markdown:
//   <Cast src="/casts/linux/ftrace-function-graph.cast"
//         caption="Following a read() with the function-graph tracer" />
export default function Cast({ src, caption, poster = "npt:0:01" }) {
  const containerRef = useRef(null);
  const resolved = useBaseUrl(src);

  useEffect(() => {
    let player;
    let cancelled = false;

    (async () => {
      const AsciinemaPlayer = (await import("asciinema-player")).default;
      if (cancelled || !containerRef.current) return;
      player = AsciinemaPlayer.create(resolved, containerRef.current, {
        autoPlay: false,
        idleTimeLimit: 2,
        fit: "width",
        theme: "asciinema",
        poster,
      });
    })();

    return () => {
      cancelled = true;
      player?.dispose?.();
    };
  }, [resolved, poster]);

  return (
    <figure className="kb-cast">
      <div className="kb-cast__player" ref={containerRef} />
      {caption && (
        <figcaption className="kb-cast__caption">{caption}</figcaption>
      )}
    </figure>
  );
}
