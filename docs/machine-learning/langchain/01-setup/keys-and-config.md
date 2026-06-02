---
id: keys-and-config
title: Keys & Config
sidebar_label: Keys & Config
sidebar_position: 3
tags: [langchain, configuration, api-keys, environment, security]
---

# Keys & Config

LangChain reads provider credentials from environment variables by default. The standard pattern is a `.env` file loaded with `python-dotenv`, never a key typed directly into source.

```bash
pip install -U python-dotenv
```

```bash title=".env"
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

```python
from dotenv import load_dotenv

load_dotenv()  # reads .env into os.environ before anything else runs
```

## Environment variable names

| Provider | Env var |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google (Gemini) | `GOOGLE_API_KEY` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| Fireworks | `FIREWORKS_API_KEY` |
| Ollama (hosted) | `OLLAMA_API_KEY` |

Once the relevant variable is set, `init_chat_model` picks it up with no explicit key argument:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai")
response = model.invoke("Say hello in one word.")
print(response.content)
```

`model_provider` makes the provider explicit rather than inferred from the model name — swap it and the model string to target a different provider without touching the rest of your code.

:::danger
- Never commit a `.env` file — add it to `.gitignore` before the first commit, not after.
- Never interpolate an API key into a prompt string; a key that reaches the model can leak into a trace or a logged completion.
- Set a spend cap on the provider dashboard before running any agent loop. An agent that retries or loops unexpectedly turns a typo into a bill, not just a bug.
:::

## See also

- [Installation](./installation.md) — installing the packages these env vars configure.
- [Chat models](../02-core-primitives/chat-models.md) — the full `init_chat_model` parameter surface.
- [Security](../10-deployment/security.md) — secret handling in production deployments.
