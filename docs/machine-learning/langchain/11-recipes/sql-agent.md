---
id: sql-agent
title: SQL Agent
sidebar_label: SQL Agent
sidebar_position: 2
tags: [langchain, sql, agent, recipe]
---

# SQL Agent

An agent that answers questions over a database: it introspects the schema, writes a query, runs it, and reasons over the result — the [tool-calling loop](../06-tools-and-agents/tool-calling.md) applied to `SELECT` statements.

```python
from langchain.agents import create_agent
from sqlalchemy import create_engine, inspect, text

engine = create_engine("postgresql://readonly_user:***@localhost/reports")


def list_tables() -> str:
    """List every table available to query."""
    return ", ".join(inspect(engine).get_table_names())


def describe_table(table_name: str) -> str:
    """Show column names and types for one table."""
    columns = inspect(engine).get_columns(table_name)
    return "\n".join(f"{c['name']}: {c['type']}" for c in columns)


def run_query(sql: str) -> str:
    """Run a read-only SQL query and return up to 20 rows."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchmany(20)
        return "\n".join(str(row) for row in rows) or "No rows returned."


agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[list_tables, describe_table, run_query],
    system_prompt=(
        "You answer questions by querying a SQL database. Always call "
        "list_tables and describe_table before writing a query against "
        "a table you haven't seen yet. Use only SELECT statements."
    ),
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "How many orders shipped last month?"}]
})
print(result["messages"][-1].content)
```

```mermaid
sequenceDiagram
    participant U as User
    participant M as Model
    participant DB as Database (read-only role)
    U->>M: "How many orders shipped last month?"
    M->>DB: list_tables()
    DB-->>M: table names
    M->>DB: describe_table("orders")
    DB-->>M: column names, types
    M->>DB: run_query("SELECT COUNT(*) ...")
    DB-->>M: row count
    M->>U: answer
```

:::danger
Connect with a database role that has `SELECT`-only grants, not the role your application writes with. The system prompt says "use only SELECT statements," but a prompt is a suggestion the model can be talked out of — the database permission is what actually stops a generated `DROP TABLE` or `DELETE` from running. Treat every model-generated query as untrusted input, the same way you would a query built from raw user input in any other context.
:::

## See also

- [Tool Calling](../06-tools-and-agents/tool-calling.md) — the request/execute/observe loop this agent runs.
- [Custom Tools](../06-tools-and-agents/custom-tools.md) — why each tool's docstring matters here as much as its code.
- [Security](../10-deployment/security.md) — treating tool output and tool-triggered side effects as untrusted.
