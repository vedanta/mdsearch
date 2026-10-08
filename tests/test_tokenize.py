from mdsearch import tokenize


def test_lowercases_and_splits_on_non_word_characters():
    assert tokenize("Hello, World! hello_world 42") == ["hello", "world", "hello_world", "42"]


def test_unicode_letters_are_word_characters():
    assert tokenize("Café naïve—crème") == ["café", "naïve", "crème"]


def test_empty_and_punctuation_only():
    assert tokenize("") == []
    assert tokenize(" ,.;!? ") == []
