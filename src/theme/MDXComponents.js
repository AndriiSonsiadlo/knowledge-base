import MDXComponents from "@theme-original/MDXComponents";
import lucideSubset from "@site/src/components/lucide-subset.json";

// Offline <Icon /> for MDX. Renders a bundled Iconify icon body as an inline SVG,
// synchronously at build time (SSR) — no runtime API, no hydration placeholder.
// Icons live in src/components/lucide-subset.json (regenerate via `npm run gen-icons`).
// Usage in markdown:  <Icon icon="lucide:rocket" />
function Icon({ icon, inline, ...rest }) {
	const name = String(icon).replace(/^lucide:/, "");
	const data = lucideSubset.icons[name];
	if (!data) return null;
	const w = data.width ?? lucideSubset.width;
	const h = data.height ?? lucideSubset.height;
	return (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="1em"
			height="1em"
			viewBox={`0 0 ${w} ${h}`}
			aria-hidden="true"
			style={{ display: "inline-block", verticalAlign: "-0.125em" }}
			// biome-ignore lint/security/noDangerouslySetInnerHtml: trusted, build-time icon data
			dangerouslySetInnerHTML={{ __html: data.body }}
			{...rest}
		/>
	);
}

export default {
	...MDXComponents,
	Icon,
};
