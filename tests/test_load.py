import pytest

from mdsearch import Document, load_documents
from conftest import write_tree


def test_loads_markdown_recursively_sorted_skipping_hidden(corpus):
    docs = load_documents(corpus)
    assert [d.path for d in docs] == ["a.md", "b.md", "d.MD", "sub/c.md"]
    assert all(isinstance(d, Document) for d in docs)


def test_text_is_whole_file(corpus):
    docs = {d.path: d for d in load_documents(corpus)}
    assert docs["b.md"].text == "# Beta Notes\nA fox appears once here, with cats and dogs.\n"


def test_titles(corpus):
    titles = {d.path: d.title for d in load_documents(corpus)}
    assert titles["a.md"] == "Alpha Guide"
    assert titles["sub/c.md"] == "Gamma"          # first level-1 heading, not on line 1
    assert titles["d.MD"] == "d"                  # "##" is not level 1: falls back to the stem


def test_title_strips_trailing_hashes_and_requires_space(tmp_path):
    write_tree(tmp_path, {
        "x.md": "# Closed Heading ##\nbody\n",
        "y.md": "#NoSpace\nbody\n",
        "z.md": "#   \n# Real\n",
    })
    titles = {d.path: d.title for d in load_documents(tmp_path)}
    assert titles == {"x.md": "Closed Heading", "y.md": "y", "z.md": "Real"}


def test_undecodable_bytes_do_not_raise(tmp_path):
    write_tree(tmp_path, {"bad.md": b"# Bad \xff\xfe bytes\nfox\n"})
    [doc] = load_documents(tmp_path)
    assert "fox" in doc.text


def test_missing_root_raises(tmp_path):
    with pytest.raises(NotADirectoryError):
        load_documents(tmp_path / "nope")
