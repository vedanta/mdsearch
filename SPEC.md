# mdsearch specification

`mdsearch` is a small Python command-line tool that searches a folder of Markdown files by keyword and ranks the results with BM25.

The acceptance tests in `tests/` decide whether an implementation is correct. **Do not modify anything under `tests/`.**

## Layout and environment

- Python 3.13, standard library only (no runtime dependencies). `pytest` is the only development dependency and is already declared.
- The implementation is a package named `mdsearch` at the repository root (`mdsearch/__init__.py`), runnable as `python -m mdsearch` (`mdsearch/__main__.py`).
- Run the tests with `uv run pytest`.

## Python API

Everything below is importable from `mdsearch`.

### `tokenize(text: str) -> list[str]`

Lowercase the text with `str.lower()`, then return every match of the regular expression `\w+`, in order. Underscores and digits are part of words, and non-ASCII letters are handled the way Python's `re` handles `\w` on `str`.

```python
tokenize("Hello, World! hello_world 42")  # ["hello", "world", "hello_world", "42"]
```

### `Document`

A dataclass with three `str` fields:

| Field | Meaning |
|---|---|
| `path` | Path relative to the searched root, with `/` separators |
| `title` | See "Titles" |
| `text` | The whole file contents |

### `load_documents(root: str | os.PathLike) -> list[Document]`

- Walk `root` recursively. Load every file whose name ends in `.md`, ignoring case (`.md`, `.MD`).
- Skip any file or directory whose name starts with `.`, and everything below such a directory.
- Read files as UTF-8 with `errors="replace"`; an undecodable byte never raises.
- Return the documents sorted by `path`.
- Raise `NotADirectoryError` if `root` does not exist or is not a directory.

### Titles

A line is a level-1 ATX heading if it matches `^#[ \t]+(.+)$`: `#`, then at least one space or tab, then text. `## Heading` is not level 1, and neither is `#Heading`. Its heading text is the captured group with surrounding whitespace stripped, then trailing `#` characters removed, then whitespace stripped again (`# Closed Heading ##` gives `Closed Heading`).

The title is the heading text of the first level-1 heading in the file whose heading text is not empty; headings whose text is empty are skipped. If there is none, the title is the file name without its extension (`notes.md` gives `notes`, `d.MD` gives `d`).

### `Result`

A dataclass with fields `path: str`, `title: str`, `score: float` and `snippet: str`.

### `search(docs: list[Document], query: str, limit: int = 10) -> list[Result]`

Rank `docs` against `query` with BM25:

- **Query terms** are the *distinct* tokens of `tokenize(query)`. A term repeated in the query counts once. If there are none, return `[]`.
- **Document length** `dl` is `len(tokenize(doc.text))`. `avgdl` is the mean `dl` over all of `docs`; if it is 0, use 1.
- `N` is `len(docs)`. For a term `t`, `df(t)` is the number of documents whose tokens contain `t`, and `tf(t, d)` is how many times `t` occurs in the tokens of document `d`.
- With `k1 = 1.2` and `b = 0.75`:

  ```
  idf(t)      = ln( (N - df(t) + 0.5) / (df(t) + 0.5) + 1 )
  score(d, q) = sum over query terms t of
                idf(t) * tf(t, d) * (k1 + 1) / ( tf(t, d) + k1 * (1 - b + b * dl / avgdl) )
  ```

- Leave out documents that contain no query term (score 0).
- Sort by score descending, then by `path` ascending. Return at most `limit` results.
- `score` is the unrounded float.

**Snippet.** Find the earliest position in `doc.text` where any query term occurs as a whole word, ignoring case: the regular expression `(?<!\w)` + `re.escape(term)` + `(?!\w)` with `re.IGNORECASE`. Take the slice from `max(0, pos - 30)` to `max(0, pos - 30) + 80`. Replace every run of whitespace, newlines included, with a single space, and strip the ends. Prefix `…` (U+2026) if the slice does not start at 0, and suffix `…` if it ends before the end of the text. So a snippet is at most 82 characters, contains the matched term, and has no newline.

## Command line

```
python -m mdsearch DIR QUERY [--limit N] [--json]
```

| Argument | Meaning |
|---|---|
| `DIR` | Folder to search |
| `QUERY` | Query string (quote it if it has spaces) |
| `--limit N` | Maximum number of results, default 10; must be an integer of at least 1 |
| `--json` | Print JSON instead of text |

**Text output.** Two lines per result, in rank order:

```
{score:.3f}\t{path}\t{title}
\t{snippet}
```

**JSON output.** One JSON array printed to stdout, one object per result in rank order, with keys `path`, `title`, `score` (rounded to 3 decimal places with `round(score, 3)`) and `snippet`. Use `ensure_ascii=False`.

**Exit codes and errors.**

| Situation | stdout | stderr | Exit code |
|---|---|---|---|
| At least one result | the results | nothing | 0 |
| No results (including an empty query or an empty folder) | nothing in text mode; `[]` with `--json` | `no results` | 1 |
| `DIR` missing or not a directory | nothing | a message starting with `error:` | 2 |
| Invalid arguments, including `--limit` below 1 | nothing | a usage message | 2 |
