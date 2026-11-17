"""scripts/area_from_above.py: the Sentinel-2 requests it builds, and what it writes (or refuses to write) from a stubbed service."""
import io
import json

import httpx
from PIL import Image

from app.modules.areastats.areamap import MAPS
from scripts import area_from_above as afa

KHARADI = MAPS["kharadi"].box


def png(color=(90, 110, 80, 255), size=(40, 40), patch=None):
    img = Image.new("RGBA", size, color)
    if patch:
        share, fill = patch
        for x in range(size[0]):
            for y in range(int(size[1] * share)):
                img.putpixel((x, y), fill)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def service(pictures, passes=None, seen=None):
    """A fake Copernicus: a token, a catalogue answering `passes[year]`, a Process API answering `pictures[year]`."""
    passes = passes or {}

    def handler(req: httpx.Request):
        if seen is not None:
            seen.append(req)
        if req.url == afa.TOKEN_URL:
            form = dict(x.split("=", 1) for x in req.content.decode().split("&"))
            if form.get("client_secret") != "s3cret":
                return httpx.Response(401, json={"error": "unauthorized_client", "error_description": "Invalid client secret"})
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 600})
        assert req.headers["Authorization"] == "Bearer tok"
        body = json.loads(req.content)
        if str(req.url) == afa.CATALOG_URL:
            year = int(body["datetime"][:4])
            return httpx.Response(200, json={"type": "FeatureCollection", "features": passes.get(year, [])})
        assert str(req.url) == afa.PROCESS_URL
        year = int(body["input"]["data"][0]["dataFilter"]["timeRange"]["from"][:4])
        got = pictures[year]
        return got if isinstance(got, httpx.Response) else httpx.Response(200, content=got, headers={"content-type": "image/png"})
    return httpx.Client(transport=httpx.MockTransport(handler))


def feature(day, cc):
    return {"type": "Feature", "properties": {"datetime": f"{day}T05:26:31Z", "eo:cloud_cover": cc}}


def call(tmp_path, client, years=(2017, 2026), **kw):
    lines = []
    code = afa.run("kharadi", years, client=client, client_id="id", client_secret=kw.pop("secret", "s3cret"), out=tmp_path,
                   echo=lines.append, **kw)
    return code, lines


def test_requests_ask_for_the_least_cloudy_true_colour_pass_of_the_dry_season():
    q = afa.catalog_query(KHARADI, 2017)
    s, w, n, e = KHARADI
    assert q["collections"] == ["sentinel-2-l2a"] and q["bbox"] == [w, s, e, n]
    assert q["datetime"] == "2017-02-01T00:00:00Z/2017-04-30T23:59:59Z" and q["filter"] == "eo:cloud_cover < 10"
    assert q["filter-lang"] == "cql2-text"   # the POST body would otherwise be read as cql2-json (the OpenAPI file)
    p = afa.process_request(KHARADI, "2017-03-12T00:00:00Z", "2017-03-12T23:59:59Z")
    data = p["input"]["data"][0]
    assert data["type"] == "sentinel-2-l2a" and p["input"]["bounds"]["bbox"] == [w, s, e, n]
    assert data["dataFilter"] == {"timeRange": {"from": "2017-03-12T00:00:00Z", "to": "2017-03-12T23:59:59Z"},
                                  "maxCloudCoverage": 10, "mosaickingOrder": "leastCC"}
    assert p["output"]["width"] == 1000 and 900 < p["output"]["height"] < 1000   # Kharadi's box is a little taller than wide
    assert p["output"]["responses"] == [{"identifier": "default", "format": {"type": "image/png"}}]
    assert '"B04", "B03", "B02", "dataMask"' in p["evalscript"]


def test_the_least_cloudy_pass_wins_and_the_earlier_day_on_a_tie():
    assert afa.best_pass([feature("2017-04-20", 3.1), feature("2017-03-12", 0.4), feature("2017-02-10", 0.4)]) == ("2017-02-10", 0.4)
    assert afa.best_pass([{"properties": {"datetime": "2017-03-01T05:00:00Z"}}]) is None   # no cloud figure: not judged


def test_two_clear_years_write_two_pictures_and_the_sidecar(tmp_path):
    seen = []
    client = service({2017: png(), 2026: png((120, 120, 120, 255))},
                     {2017: [feature("2017-04-01", 2.0), feature("2017-03-12", 0.4)], 2026: [feature("2026-02-18", 1.25)]}, seen)
    code, lines = call(tmp_path, client)
    assert code == 0
    for y in (2017, 2026):
        with Image.open(tmp_path / f"kharadi-{y}.webp") as img:
            assert img.format == "WEBP" and img.size == (40, 40)   # as the (stubbed) service sent it
    side = json.loads((tmp_path / "kharadi.json").read_text())
    assert side["area"] == "kharadi" and side["box"] == list(KHARADI)
    first, last = side["pictures"]
    assert first["year"] == 2017 and first["captured"] == {"from": "2017-03-12", "to": "2017-03-12"}
    assert first["month"] == "March 2017" and first["src"] == "/areas/kharadi-2017.webp" and first["cloud_filter_pct"] == 10
    assert first["credit"] == "Contains modified Copernicus Sentinel data 2017" and (first["width"], first["height"]) == (40, 40)
    assert last["month"] == "February 2026" and last["tile_cloud_pct"] == 1.2
    process = [json.loads(r.content) for r in seen if str(r.url) == afa.PROCESS_URL]
    assert process[0]["input"]["data"][0]["dataFilter"]["timeRange"]["from"] == "2017-03-12T00:00:00Z"   # the day found


def test_a_cloudy_or_empty_year_writes_nothing_and_says_why(tmp_path):
    client = service({2017: png(patch=(0.5, (250, 250, 250, 255))), 2018: png(patch=(0.3, (0, 0, 0, 0))),
                      2019: b"", 2020: httpx.Response(400, json={"error": {"status": 400, "message": "Invalid bbox"}})},
                     {y: [feature(f"{y}-03-01", 1.0)] for y in (2017, 2018, 2019, 2020)})
    code, lines = call(tmp_path, client, years=(2016, 2017, 2018, 2019, 2020))
    assert code == 1
    assert list(tmp_path.iterdir()) == []                         # no picture, no sidecar
    said = "\n".join(lines)
    assert "2016: no picture written: no pass under 10% cloud" in said
    assert "2017: no picture written: cloud over about 50% of the box" in said
    assert "2018: no picture written: the pass leaves 30% of the box without data" in said
    assert "2019: no picture written: the Process API answered with an empty picture" in said
    assert "2020: no picture written: the Process API failed (HTTP 400: Invalid bbox)" in said


def test_a_rerun_keeps_the_other_years_in_the_sidecar(tmp_path):
    call(tmp_path, service({2017: png()}, {2017: [feature("2017-03-12", 0.4)]}), years=(2017,))
    code, _ = call(tmp_path, service({2026: png()}, {2026: [feature("2026-03-05", 0.2)]}), years=(2026,))
    assert code == 0
    assert [p["year"] for p in json.loads((tmp_path / "kharadi.json").read_text())["pictures"]] == [2017, 2026]


def test_a_refused_key_writes_nothing(tmp_path):
    code, lines = call(tmp_path, service({}), secret="wrong")
    assert code == 1 and list(tmp_path.iterdir()) == []
    assert "refused the client id and secret (HTTP 401: Invalid client secret)" in lines[0]


def test_dry_run_prints_the_requests_and_needs_no_key_or_network(tmp_path):
    def no_network(req):
        raise AssertionError("the dry run must not call out")
    lines = []
    code = afa.run("kharadi", [2017, 2026], dry_run=True, out=tmp_path, echo=lines.append,
                   client=httpx.Client(transport=httpx.MockTransport(no_network)))
    assert code == 0 and list(tmp_path.iterdir()) == []
    out = "\n".join(lines)
    assert afa.CATALOG_URL in out and afa.PROCESS_URL in out and '"mosaickingOrder": "leastCC"' in out
    assert '"datetime": "2026-02-01T00:00:00Z/2026-04-30T23:59:59Z"' in out
    assert afa.main(["kharadi", "--dry-run", "--years", "2017", "--out", str(tmp_path)]) == 0


def test_an_area_without_a_map_box_needs_one_given():
    lines = []
    assert afa.run("baner", [2017], dry_run=True, echo=lines.append) == 1 and "pass --box" in lines[0]
    lines.clear()
    assert afa.run("baner", [2017], afa.parse_box("18.545,73.765,18.580,73.800"), dry_run=True, echo=lines.append) == 0
    assert "[\n    73.765,\n    18.545,\n    73.8,\n    18.58\n  ]" in "\n".join(lines)
    assert afa.run("mundhwa", [2017], dry_run=True, echo=lines.append) == 1
