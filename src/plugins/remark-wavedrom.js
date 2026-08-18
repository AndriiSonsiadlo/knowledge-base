import JSON5 from "json5";
import onml from "onml";
import { visit } from "unist-util-visit";
import wavedrom from "wavedrom";

// Build-time WaveDrom rendering. Turns ```wavedrom fences into pre-rendered
// SVG carried by the <WaveDrom /> MDX component (src/components/WaveDrom).
//
// The node MUST be an mdxJsxFlowElement, never a raw `html` node: WaveDrom's
// skin embeds a <style> block containing CSS braces, which MDX v3 would parse
// as a JSX expression and fail the build on.
//
// Fence meta: ```wavedrom title="SPI mode 0" alt="SPI mode 0 timing"

const META_PAIR = /(\w+)="([^"]*)"/g;

function parseMeta(meta) {
  const parsed = {};
  if (!meta) return parsed;
  for (const [, key, value] of meta.matchAll(META_PAIR)) {
    parsed[key] = value;
  }
  return parsed;
}

export default function remarkWavedrom() {
  return (tree, file) => {
    // renderAny uses this to namespace generated element ids; it only has to be
    // unique within one page, and the transformer runs once per file.
    let diagramIndex = 0;

    visit(tree, "code", (node, index, parent) => {
      if (node.lang !== "wavedrom" || !parent) return;

      const { title, alt } = parseMeta(node.meta);
      const label = alt || title;
      if (!label) {
        file.fail(
          'wavedrom fence needs alt="..." (or title="..." to fall back to)',
          node,
        );
      }

      let source;
      try {
        source = JSON5.parse(node.value);
      } catch (error) {
        file.fail(`wavedrom fence is not valid JSON5: ${error.message}`, node);
      }

      const svg = onml.stringify(
        wavedrom.renderAny(diagramIndex, source, wavedrom.waveSkin),
      );
      diagramIndex += 1;

      const attributes = [
        { type: "mdxJsxAttribute", name: "svg", value: svg },
        { type: "mdxJsxAttribute", name: "alt", value: label },
      ];
      if (title) {
        attributes.push({
          type: "mdxJsxAttribute",
          name: "caption",
          value: title,
        });
      }

      parent.children[index] = {
        type: "mdxJsxFlowElement",
        name: "WaveDrom",
        attributes,
        children: [],
      };
    });
  };
}
