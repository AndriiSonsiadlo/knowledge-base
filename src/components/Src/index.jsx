import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { srcHref, srcLabel } from "@lib/kernelSource";

// <Src /> — an inline reference into the pinned kernel source.
//
// Usage in markdown:
//   Path resolution happens in <Src file="fs/namei.c" symbol="path_openat" />.
//   The allocator lives in <Src file="mm/page_alloc.c" />.
//   <Src symbol="handle_mm_fault" /> is the entry point.
//
// Never hand-write an elixir.bootlin.com URL in a page — the version would
// then be duplicated across hundreds of files.
export default function Src({ file, symbol }) {
  const { siteConfig } = useDocusaurusContext();
  const version = siteConfig.customFields.linuxKernelVersion;
  return (
    <a
      className="kb-src"
      href={srcHref(version, { file, symbol })}
      target="_blank"
      rel="noopener noreferrer"
    >
      <code>{srcLabel({ file, symbol })}</code>
    </a>
  );
}
