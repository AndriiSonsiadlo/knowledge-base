// <WaveDrom /> — a WaveDrom timing waveform or register bit-field strip,
// rendered to SVG at build time by src/plugins/remark-wavedrom.js. Nothing
// renders on the client; this component only places the finished SVG.
//
// WaveDrom's default skin draws black strokes on a transparent canvas, so the
// diagram sits on the same permanent light plate <Figure /> uses for
// third-party technical diagrams. See src/components/Figure/index.js.
//
// Authored in markdown as:
//   ```wavedrom title="SPI mode 0" alt="SPI mode 0 timing"
//   { signal: [ ... ] }
//   ```
export default function WaveDrom({ svg, alt, caption }) {
  return (
    <figure className="kb-figure kb-wavedrom">
      <div
        className="kb-figure__plate"
        role="img"
        aria-label={alt}
        // biome-ignore lint/security/noDangerouslySetInnerHtml: trusted, build-time WaveDrom output
        dangerouslySetInnerHTML={{ __html: svg }}
      />
      {caption && (
        <figcaption className="kb-figure__caption">{caption}</figcaption>
      )}
    </figure>
  );
}
