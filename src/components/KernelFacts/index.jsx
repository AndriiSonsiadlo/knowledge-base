import { formatRecallText } from "@lib/recallFormat";

// <KernelFacts /> — the fixed card that ends every docs/linux/ topic page.
//
// Four rows, always the same four, always in this order, so a returning reader
// finds what they need by position rather than by reading: the structure that
// matters, the code path, the command that shows it on a live system, and the
// one belief most people hold that is wrong.
//
// Props are plain strings, not markdown, so backtick spans are rendered here
// the same way <Recall /> does it.
//
// Usage in markdown:
//   <KernelFacts
//     structure={[["struct vm_area_struct", "include/linux/mm_types.h"]]}
//     path="do_page_fault() → handle_mm_fault() → handle_pte_fault()"
//     observe="perf trace -e 'exceptions:page_fault_user' -p $(pgrep -n bash)"
//     trap="A major fault is not a worse fault. It is a fault that needed I/O." />
function Formatted({ text, className }) {
  return (
    <span
      className={className}
      // biome-ignore lint/security/noDangerouslySetInnerHtml: trusted doc content, rendered at build time
      dangerouslySetInnerHTML={{ __html: formatRecallText(text) }}
    />
  );
}

export default function KernelFacts({ structure = [], path, observe, trap }) {
  if (!path || !observe || !trap) {
    throw new Error("<KernelFacts> requires `path`, `observe`, and `trap`");
  }
  return (
    <aside className="kb-kernel-facts">
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Structure</span>
        <div className="kb-kernel-facts__structure">
          {structure.map(([name, header]) => (
            <div key={name}>
              <Formatted text={`\`${name}\``} />
              {header && (
                <Formatted
                  className="kb-kernel-facts__header"
                  text={` — \`${header}\``}
                />
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Path</span>
        <Formatted text={path} />
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Observe</span>
        <Formatted text={`\`${observe}\``} />
      </div>
      <div className="kb-kernel-facts__row">
        <span className="kb-kernel-facts__label">Trap</span>
        <Formatted text={trap} />
      </div>
    </aside>
  );
}
