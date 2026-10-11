"""Photo ranking: duplicates collapse to the best copy, weak photos move back or out, the agent's order holds otherwise,
the minimum count is respected, and the hero is a well-exposed landscape photo."""
import pytest

from app.modules import photoquality
from app.modules.photoquality import dhash, duplicate_groups, hamming, pick_hero, rank_photos, ranking

from ..photo_helpers import blurred, brighter, darker, save, scene


@pytest.fixture
def pics(tmp_path):
    d = tmp_path / "images"
    return {
        "a": save(d, "a.jpg", scene(1)),
        "b": save(d, "b.jpg", scene(2)),
        "c": save(d, "c.jpg", scene(3)),
        "a_copy": save(d, "a_copy.jpg", brighter(scene(1))),
        "a_again": save(d, "a_again.jpg", scene(1)),
        "blur": save(d, "blur.jpg", blurred(scene(4))),
        "dark": save(d, "dark.jpg", darker(scene(5))),
        "tall": save(d, "tall.jpg", scene(6, (900, 1200))),
    }


def names(paths):
    return [p.stem for p in paths]


def test_public_api():
    assert {"rank_photos", "pick_hero", "duplicate_groups", "dhash", "analyze"} <= set(photoquality.__all__)


def test_dhash_is_close_for_copies_and_far_for_other_shots(pics):
    a, copy, b = dhash(pics["a"]), dhash(pics["a_copy"]), dhash(pics["b"])
    assert hamming(a, copy) <= ranking.DUP_BITS < hamming(a, b)


def test_duplicates_collapse_to_one(pics):
    p = pics
    assert names(rank_photos([p["a"], p["b"], p["a_copy"], p["c"], p["a_again"]])) == ["a", "b", "c"]
    groups = duplicate_groups([p["a"], p["b"], p["a_copy"], p["c"]])
    assert [names(g) for g in groups] == [["a", "a_copy"], ["b"], ["c"]]


def test_a_flat_colour_is_not_a_copy_of_another_colour(tmp_path):
    import numpy as np
    red = save(tmp_path, "red.jpg", np.full((900, 1200, 3), (30, 30, 200), np.uint8))
    green = save(tmp_path, "green.jpg", np.full((900, 1200, 3), (30, 200, 30), np.uint8))
    assert len(duplicate_groups([red, green])) == 2


def test_the_best_copy_is_kept_in_the_place_of_the_first(tmp_path, pics):
    soft_a = save(tmp_path, "soft_a.jpg", blurred(scene(1)))   # the same shot, out of focus
    assert names(rank_photos([soft_a, pics["b"], pics["a"]])) == ["a", "b"]


def test_a_blurry_or_dark_photo_moves_out_and_comes_back_last_only_when_needed(pics):
    p = pics
    assert names(rank_photos([p["blur"], p["a"], p["dark"], p["b"]])) == ["a", "b"]
    assert names(rank_photos([p["blur"], p["a"], p["dark"], p["b"]], min_keep=3)) == ["a", "b", "blur"]
    assert names(rank_photos([p["blur"], p["a"], p["dark"], p["b"]], min_keep=4)) == ["a", "b", "blur", "dark"]


def test_the_agents_order_is_kept_when_photos_are_equally_good(pics):
    p = pics
    assert names(rank_photos([p["c"], p["b"], p["a"]])) == ["c", "b", "a"]
    assert names(rank_photos([p["a"], p["b"], p["c"]])) == ["a", "b", "c"]
    assert names(rank_photos([p["c"], p["b"], p["a"]])) == names(rank_photos([p["c"], p["b"], p["a"]]))


def test_the_minimum_count_is_respected(pics):
    p = pics
    assert names(rank_photos([p["a"], p["a_copy"]], min_keep=2)) == ["a", "a_copy"]
    assert names(rank_photos([p["blur"], p["dark"]], min_keep=2)) == ["blur", "dark"]
    assert names(rank_photos([p["blur"], p["dark"]], min_keep=1)) == ["blur"]
    assert rank_photos([p["blur"], p["dark"]]) == []
    assert names(rank_photos([p["a"]], min_keep=5)) == ["a"]
    assert rank_photos([], min_keep=2) == []


def test_the_hero_is_a_landscape_photo_without_serious_issues(pics):
    p = pics
    assert names(rank_photos([p["tall"], p["blur"], p["b"], p["a"]])) == ["b", "tall", "a"]
    assert pick_hero([p["blur"], p["tall"], p["a"]]) == p["a"]
    assert pick_hero([p["tall"]]) == p["tall"]
    assert pick_hero([p["blur"], p["dark"]]) is None


def test_an_unreadable_file_is_left_out_unless_it_is_needed(tmp_path, pics):
    junk = tmp_path / "junk.jpg"
    junk.write_bytes(b"not a photo")
    missing = tmp_path / "missing.jpg"
    assert names(rank_photos([junk, pics["a"], missing])) == ["a"]
    assert names(rank_photos([junk, pics["a"]], min_keep=2)) == ["a", "junk"]


def test_analysis_is_cached_by_content(tmp_path, pics, monkeypatch):
    calls = []
    real = ranking.analyze
    monkeypatch.setattr(ranking, "analyze", lambda img: calls.append(1) or real(img))
    fresh = save(tmp_path, "fresh.jpg", scene(99))
    rank_photos([fresh])
    rank_photos([fresh])
    same = save(tmp_path / "other", "same.jpg", scene(99))
    rank_photos([same])
    assert len(calls) == 1
