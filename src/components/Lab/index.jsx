// <Lab /> — a hands-on block with a required host badge.
//
// The badge is required and is the point: a reader must never start a lab and
// discover four steps in that their environment cannot run it. Children are
// ordinary markdown — numbered steps, expected output, and a closing "if it
// fails" line.
//
// Usage in markdown:
//   <Lab host="qemu" title="Watch a page fault happen" time="10 min">
//   1. ...
//   </Lab>

const HOSTS = {
  qemu: "QEMU lab",
  "qemu-gdb": "QEMU + GDB",
  "any-linux": "Any Linux",
  "wsl2-ok": "WSL2 OK",
  "root-required": "Root required",
};

export default function Lab({ host, title, time, children }) {
  if (!HOSTS[host]) {
    throw new Error(
      `<Lab host="${host}"> is not a known host. Use one of: ${Object.keys(HOSTS).join(", ")}`,
    );
  }
  return (
    <section className="kb-lab">
      <header className="kb-lab__head">
        <span className={`kb-lab__host kb-lab__host--${host}`}>
          {HOSTS[host]}
        </span>
        <span className="kb-lab__title">{title}</span>
        {time && <span className="kb-lab__time">{time}</span>}
      </header>
      <div className="kb-lab__body">{children}</div>
    </section>
  );
}
