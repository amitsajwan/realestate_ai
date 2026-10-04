from app.core import areas


def test_keys_slugs_and_env_names_are_unique_and_well_formed():
    keys = [a.key for a in areas.AREAS]
    slugs = [a.slug for a in areas.AREAS]
    assert len(set(keys)) == len(keys) and len(set(slugs)) == len(slugs)
    for a in areas.AREAS:
        assert a.tier in ("affordable", "it") and a.key.isidentifier() and a.slug == a.slug.lower()
        assert a.aliases and all(al == al.lower() for al in a.aliases)
        assert a.hashtags and all(h.startswith("#") and " " not in h for h in a.hashtags)
        assert a.location_env == "IG_LOCATION_" + a.key.upper()


def test_lookup_by_key_slug_or_spoken_name():
    assert areas.get("keshav-nagar").key == "keshav_nagar"
    assert areas.get("Upper Kharadi").key == "upper_kharadi"
    assert areas.get("nowhere") is None


def test_named_in_prefers_the_specific_area():
    assert [a.key for a in areas.named_in("2 BHK in Upper Kharadi")] == ["upper_kharadi"]
    assert [a.key for a in areas.named_in("Kharadi and Upper Kharadi compared")] == ["upper_kharadi", "kharadi"]
    assert [a.key for a in areas.named_in("Homes near Hinjewadi Phase 3")] == ["hinjawadi"]
    assert [a.key for a in areas.named_in("Lohgaon airport road")] == ["lohegaon"]
    assert areas.named_in("Pune metro update") == ()
