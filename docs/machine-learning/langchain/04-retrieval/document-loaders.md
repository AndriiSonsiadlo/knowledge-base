---
id: document-loaders
title: Document Loaders
sidebar_label: Document Loaders
sidebar_position: 1
tags: [langchain, loaders, documents, pdf, ingestion]
---

# Document Loaders

Every retrieval pipeline starts by turning some external source — a PDF, a web page, a database table — into LangChain's shared unit: the `Document`.

```python
from langchain_core.documents import Document

doc = Document(
    page_content="Nike was incorporated in 1968.",
    metadata={"source": "nike-10k.pdf", "page": 4},
)
```

A `Document` is just two fields: `page_content` (the text a model will read) and `metadata` (a dict your code can filter or cite on later). Loaders exist to produce lists of these from real sources.

```python
import bs4
import requests

def load_web_page(url: str) -> list[Document]:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    return [Document(page_content=soup.get_text(), metadata={"source": url})]
```

LangChain ships loaders for most common sources under `langchain_community.document_loaders` (PDFs, CSVs, directories, cloud storage, databases); write your own the same way — one function returning `list[Document]` — whenever a source is bespoke enough that a loader isn't worth pulling in.

| Source type | Typical loader | Gotcha |
| --- | --- | --- |
| PDF | `PyPDFLoader` | Page numbers land in `metadata["page"]`, but scanned (image-only) PDFs need OCR first — plain PDF loaders return empty text. |
| Web page | `WebBaseLoader` / custom `bs4` | Boilerplate (nav, footer) pollutes chunks unless you scope the parse to the content region. |
| CSV / structured rows | `CSVLoader` | Defaults to one `Document` per row — fine for lookup, wrong for long free-text columns that need splitting too. |
| Directory of files | `DirectoryLoader` | Silently skips files it has no loader for; check the count against what you expect. |
| Database table | Custom loader over your ORM/driver | Easy to leak PII into a vector store if you select `SELECT *` without thinking about which columns are model-visible. |

:::tip
Set stable metadata (`source`, `page`, `section`) at load time. Once documents are chunked and embedded, that context is expensive to recover — the chunk itself often lost the surrounding structure that told you where it came from.
:::

## See also

- [Text Splitters](./text-splitters.md) — the next stage: turning loaded documents into chunks.
- [RAG Pipeline](./rag-pipeline.md) — where loading fits in the full load → split → embed → store → retrieve flow.
