import Figure from "@site/src/components/Figure";
import KernelFacts from "@site/src/components/KernelFacts";
import Lab from "@site/src/components/Lab";
import lucideSubset from "@site/src/components/lucide-subset.json";
import Recall from "@site/src/components/Recall";
import Src from "@site/src/components/Src";
import Video from "@site/src/components/Video";
import WaveDrom from "@site/src/components/WaveDrom";
import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";
import MDXComponents from "@theme-original/MDXComponents";

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
  Figure,
  KernelFacts,
  Lab,
  Recall,
  Src,
  Video,
  WaveDrom,
  Tabs,
  TabItem,
};
