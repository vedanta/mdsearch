# mdsearch

A benchmark task for the home-ai-factory stream: a small command-line tool that searches a folder of Markdown files by keyword and ranks results with BM25.

The task is defined by [SPEC.md](SPEC.md) and decided by the acceptance tests in `tests/`. This commit holds no implementation; every test fails until one is written.

```bash
uv run pytest
```

Agents implementing the task are given SPEC.md and the tests, and must not modify `tests/`.
