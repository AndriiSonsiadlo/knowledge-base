import useBaseUrl from "@docusaurus/useBaseUrl";

// <Figure /> — a real figure (raster/vector image), as opposed to a Mermaid diagram.
//
// Most third-party technical diagrams are black strokes on a transparent or white
// canvas, so they vanish against a dark theme. Diagrams are therefore rendered on a
// permanent light plate; photographs and screenshots opt out with `photo`.
//
// Usage in markdown:
//   <Figure src="/img/cs/cpu-architecture/pipeline.png"
//           alt="Five instructions overlapping in a five-stage pipeline"
//           caption="Five instructions in flight, one per stage."
//           source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Fivestagespipeline.png"
//           license="CC BY-SA 3.0" />
export default function Figure({
	src,
	alt,
	caption,
	source,
	href,
	license,
	photo = false,
	width,
}) {
	const resolved = useBaseUrl(src);
	return (
		<figure className="kb-figure">
			<div className={`kb-figure__plate${photo ? " kb-figure__plate--photo" : ""}`}>
				<img src={resolved} alt={alt} loading="lazy" style={width ? { maxWidth: width } : undefined} />
			</div>
			{(caption || source) && (
				<figcaption className="kb-figure__caption">
					{caption}
					{source && (
						<span className="kb-figure__credit">
							{caption ? " " : ""}
							<a href={href} target="_blank" rel="noopener noreferrer">
								{source}
							</a>
							{license ? `, ${license}` : ""}
						</span>
					)}
				</figcaption>
			)}
		</figure>
	);
}
