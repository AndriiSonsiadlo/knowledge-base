// <Video /> — an embedded talk or explainer.
//
// The video stays where it lives; this repository only ever holds a URL. Use
// it where watching genuinely beats reading, and prefer a ## References entry
// for anything much over an hour.
//
// Usage in markdown:
//   <Video src="https://www.youtube.com/embed/<id>"
//          title="Paul McKenney — RCU: what is it, and how does it work?"
//          caption="Grace periods, from the person who wrote RCU." />
export default function Video({ src, title, caption }) {
  if (!title) {
    throw new Error("<Video> requires a `title` — it is the iframe's accessible name");
  }
  return (
    <figure className="kb-video">
      <div className="kb-video__frame">
        <iframe
          src={src}
          title={title}
          loading="lazy"
          allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
      {caption && <figcaption className="kb-video__caption">{caption}</figcaption>}
    </figure>
  );
}
