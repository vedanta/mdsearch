import math
import re

import pytest

from mdsearch import Document, Result, search


def docs(*pairs):
    return [Document(path=p, title=p, text=t) for p, t in pairs]


def reference_bm25(documents, query, k1=1.2, b=0.75):
    """Independent copy of the formula in SPEC.md."""
    tok = lambda s: re.findall(r"\w+", s.lower())
    terms = set(tok(query))
    toks = [tok(d.text) for d in documents]
    n = len(documents)
    avgdl = (sum(map(len, toks)) / n) or 1
    out = {}
    for d, t in zip(documents, toks):
        s = 0.0
        for term in terms:
            tf = t.count(term)
            if not tf:
                continue
            df = sum(term in x for x in toks)
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
            s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(t) / avgdl))
        if s:
            out[d.path] = s
    return out


CORPUS = docs(
    ("a.md", "the quick brown fox jumps over the lazy dog fox fox"),
    ("b.md", "a fox appears once here with cats and dogs"),
    ("c.md", "nothing about animals here just cats"),
    ("d.md", "delta zebra zebra"),
)


def test_scores_match_the_formula():
    got = {r.path: r.score for r in search(CORPUS, "fox cats", limit=10)}
    want = reference_bm25(CORPUS, "fox cats")
    assert set(got) == set(want)
    for path, score in want.items():
        assert got[path] == pytest.approx(score, rel=1e-9)


def test_returns_result_objects_ranked_by_score():
    results = search(CORPUS, "fox")
    assert all(isinstance(r, Result) for r in results)
    assert [r.path for r in results] == ["a.md", "b.md"]
    assert results[0].score > results[1].score > 0


def test_rarer_terms_weigh_more():
    corpus = docs(("x.md", "common rare"), ("y.md", "common common"), ("z.md", "common filler"))
    [top, *_] = search(corpus, "common rare")
    assert top.path == "x.md"


def test_ties_break_by_path():
    corpus = docs(("b.md", "same words"), ("a.md", "same words"), ("c.md", "other"))
    assert [r.path for r in search(corpus, "same")] == ["a.md", "b.md"]


def test_no_match_empty_query_and_empty_corpus():
    assert search(CORPUS, "unicorn") == []
    assert search(CORPUS, "  ?!  ") == []
    assert search([], "fox") == []


def test_repeated_query_terms_count_once():
    one = {r.path: r.score for r in search(CORPUS, "fox")}
    three = {r.path: r.score for r in search(CORPUS, "fox Fox FOX")}
    assert one == pytest.approx(three)


def test_limit():
    corpus = docs(*[(f"{i:02}.md", "fox") for i in range(15)])
    assert len(search(corpus, "fox")) == 10
    assert [r.path for r in search(corpus, "fox", limit=3)] == ["00.md", "01.md", "02.md"]


def test_snippet_shape():
    text = ("Intro line.\n\n" + "filler " * 20 + "\nThe Zebra crossed the road.\n" + "more " * 30)
    [r] = search(docs(("z.md", text), ("y.md", "nothing")), "zebra")
    assert "zebra" in r.snippet.lower()
    assert "\n" not in r.snippet and "  " not in r.snippet
    assert r.snippet.startswith("…") and r.snippet.endswith("…")
    assert len(r.snippet) <= 82


def test_snippet_uses_earliest_whole_word_match():
    text = "zebras are not it. Cats first, then zebra."
    [r] = search(docs(("z.md", text), ("y.md", "x")), "zebra cats")
    assert r.snippet == "zebras are not it. Cats first, then zebra."
