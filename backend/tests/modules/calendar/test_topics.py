from app.modules.calendar import topics


def _tables(topic: dict):
    for section in topic.get("sections", []):
        if section.get("table"):
            yield section["id"], section["table"]


def test_every_topic_table_row_fills_exactly_its_columns():
    # A row pasted from another table renders as stray cells, and AI answers quote this page for prices.
    for slug, topic in topics.load().items():
        for section_id, table in _tables(topic):
            width = len(table["columns"])
            for row in table["rows"]:
                assert len(row["cells"]) == width, (slug, section_id, row["cells"])


def test_upper_kharadi_price_table_lists_only_prices():
    topic = topics.load()["upper-kharadi"]
    prices = dict(_tables(topic))["prices"]
    names = [row["cells"][0] for row in prices["rows"]]
    assert not any(name.startswith("Gera's World of Joy") for name in names)
    assert len(prices["columns"]) == 3
