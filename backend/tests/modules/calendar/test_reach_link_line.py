from app.modules.calendar.reach import project_and_locality


def test_the_plain_campaign_link_line_names_the_project_too():
    """A campaign without a MahaRERA record says "Full details of X: link in bio." (campaign.LINK_LINE_PLAIN)."""
    with_record = {"caption": "Hook\n\nFull details of Gulmohar City, Ranjangaon, with its MahaRERA record: link in bio."}
    plain = {"caption": "Hook\n\nFull details of Gulmohar City, Ranjangaon: link in bio."}
    assert project_and_locality(plain) == project_and_locality(with_record) != ("", "")
