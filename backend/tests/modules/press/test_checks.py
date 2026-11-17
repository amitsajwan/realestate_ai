from app.modules.press.checks import BODY_WORDS_MAX, SUBJECT_MAX, facts_corpus, problems_in

FACTS = [{"text": "Kharadi registered 4 new MahaRERA projects in October 2026, and 11 so far in 2026.", "as_of": "2026-11-17"}]


def test_a_clean_draft_passes():
    corpus = facts_corpus(FACTS)
    assert problems_in("Pune MahaRERA data", "Kharadi registered 4 new projects in October 2026.", corpus) == []


def test_a_number_not_in_the_facts_is_a_problem():
    corpus = facts_corpus(FACTS)
    problems = problems_in("Pune data", "Kharadi registered 99 new projects.", corpus)
    assert any("number not in facts" in p for p in problems)


def test_a_sales_word_is_a_problem():
    corpus = facts_corpus(FACTS)
    assert "sales word" in problems_in("The best Pune data", "Kharadi registered 4 new projects.", corpus)


def test_subject_and_body_length_limits():
    corpus = facts_corpus(FACTS)
    assert "subject too long" in problems_in("x" * (SUBJECT_MAX + 1), "short body", corpus)
    assert "body too long" in problems_in("subject", "word " * (BODY_WORDS_MAX + 1), corpus)


def test_empty_subject_or_body_is_a_problem():
    corpus = facts_corpus(FACTS)
    assert "subject too long" in problems_in("", "a body", corpus)
    assert "body too long" in problems_in("a subject", "", corpus)
