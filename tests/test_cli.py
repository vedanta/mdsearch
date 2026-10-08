import json

from conftest import write_tree


def test_text_output(corpus, run_cli):
    p = run_cli(corpus, "fox")
    assert p.returncode == 0, p.stderr
    lines = p.stdout.splitlines()
    assert len(lines) == 4
    score, path, title = lines[0].split("\t")
    assert (path, title) == ("a.md", "Alpha Guide")
    assert len(score.split(".")[1]) == 3 and float(score) > 0
    assert lines[1].startswith("\t") and "fox" in lines[1].lower()
    assert lines[2].split("\t")[1:] == ["b.md", "Beta Notes"]


def test_json_output_and_limit(corpus, run_cli):
    p = run_cli(corpus, "fox cats", "--json", "--limit", "2")
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert [d["path"] for d in data] == ["b.md", "a.md"]   # b matches both terms
    assert set(data[0]) == {"path", "title", "score", "snippet"}
    assert data[0]["score"] == round(data[0]["score"], 3)


def test_json_keeps_unicode(tmp_path, run_cli):
    write_tree(tmp_path, {"menu.md": "# Café Menu\ncrème brûlée\n"})
    p = run_cli(tmp_path, "crème", "--json")
    assert p.returncode == 0, p.stderr
    assert "Café Menu" in p.stdout


def test_no_results(corpus, tmp_path, run_cli):
    p = run_cli(corpus, "unicorn")
    assert (p.returncode, p.stdout) == (1, "")
    assert "no results" in p.stderr
    p = run_cli(corpus, "unicorn", "--json")
    assert p.returncode == 1 and json.loads(p.stdout) == []
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run_cli(empty, "fox").returncode == 1


def test_bad_directory(tmp_path, run_cli):
    p = run_cli(tmp_path / "missing", "fox")
    assert p.returncode == 2 and p.stdout == ""
    assert p.stderr.startswith("error:")


def test_invalid_limit(corpus, run_cli):
    assert run_cli(corpus, "fox", "--limit", "0").returncode == 2
    assert run_cli(corpus, "fox", "--limit", "x").returncode == 2
