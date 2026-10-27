"""Area and network lookup from DB-IP's files (platform/geoip.py): names people know, robots by network, never raises."""
import gzip
import os
from datetime import datetime, timedelta

import httpx
import pytest

from app.platform import geoip
from app.platform.geoip import GeoIP, is_data_centre, network_name

NOW = datetime(2026, 10, 27, 9, 0)
CITY = {"city": {"names": {"en": "Pune"}}, "subdivisions": [{"names": {"en": "Maharashtra"}}], "country": {"iso_code": "IN"}}


class FakeReader:
    def __init__(self, data):
        self.data = data

    def get(self, ip):
        return self.data.get(ip)

    def close(self):
        pass


@pytest.fixture
def files(tmp_path, monkeypatch):
    """Two 'files' on disk whose content the fake reader serves, keyed by the file name."""
    content = {"dbip-city-lite.mmdb": {"49.36.1.1": CITY, "34.1.1.1": {"city": {"names": {"en": "Mumbai"}}}},
               "dbip-asn-lite.mmdb": {"49.36.1.1": {"autonomous_system_organization": "Reliance Jio Infocomm Limited"},
                                      "34.1.1.1": {"autonomous_system_organization": "Google LLC"}}}
    for name in content:
        (tmp_path / name).write_bytes(b"x")
    monkeypatch.setattr(geoip.maxminddb, "open_database", lambda path: FakeReader(content[os.path.basename(path)]))
    return tmp_path


def test_networks_read_as_the_names_people_know():
    assert network_name("Reliance Jio Infocomm Limited") == "Jio"
    assert network_name("Bharti Airtel Ltd.") == "Airtel"
    assert network_name("Vodafone Idea Ltd") == "Vi"
    assert network_name("Atria Convergence Technologies Pvt. Ltd.") == "ACT Fibernet"
    assert network_name("Sify Technologies Limited") == "Sify Technologies"
    assert network_name(None) is None


def test_cloud_networks_are_robots_and_privacy_relays_are_not():
    assert is_data_centre("Google LLC") and is_data_centre("Amazon.com, Inc.") and is_data_centre("Hetzner Online GmbH")
    assert not is_data_centre("Cloudflare, Inc.") and not is_data_centre("Akamai Technologies") and not is_data_centre("Reliance Jio")


def test_a_lookup_gives_city_region_network_and_robot(files):
    g = GeoIP(files)
    p = g.lookup("49.36.1.1")
    assert (p.city, p.region, p.country, p.network, p.robot) == ("Pune", "Maharashtra", "IN", "Jio", False)
    assert g.lookup("34.1.1.1").robot is True


def test_private_and_broken_addresses_and_missing_files_give_nothing(files, tmp_path):
    g = GeoIP(files)
    assert g.lookup("10.0.0.5") is None and g.lookup("127.0.0.1") is None and g.lookup("not-an-ip") is None and g.lookup(None) is None
    assert GeoIP(tmp_path / "nowhere").lookup("49.36.1.1") is None


def test_a_file_that_will_not_open_gives_nothing_instead_of_failing(tmp_path, monkeypatch):
    (tmp_path / "dbip-city-lite.mmdb").write_bytes(b"x")

    def broken(path):
        raise ValueError("bad file")
    monkeypatch.setattr(geoip.maxminddb, "open_database", broken)
    assert GeoIP(tmp_path).lookup("49.36.1.1") is None


def test_files_are_stale_when_missing_or_over_35_days_old(tmp_path):
    assert geoip.stale(tmp_path, lambda: NOW)
    for name in geoip.FILES.values():
        (tmp_path / name).write_bytes(b"x")
    assert not geoip.stale(tmp_path, datetime.utcnow)
    assert geoip.stale(tmp_path, lambda: datetime.utcnow() + timedelta(days=36))


def _server(available, body=b"mmdb"):
    asked = []

    def handle(req):
        asked.append(str(req.url))
        if any(m in str(req.url) for m in available):
            return httpx.Response(200, content=gzip.compress(body))
        return httpx.Response(404)
    return httpx.AsyncClient(transport=httpx.MockTransport(handle)), asked


async def test_refresh_takes_last_months_file_while_this_months_is_not_out(tmp_path, monkeypatch):
    monkeypatch.setattr(geoip.maxminddb, "open_database", lambda path: FakeReader({}))
    client, asked = _server(["2026-09"])
    assert await geoip.refresh(tmp_path, client, now=lambda: NOW) is True
    assert (tmp_path / "dbip-city-lite.mmdb").read_bytes() == b"mmdb" and (tmp_path / "dbip-asn-lite.mmdb").exists()
    assert asked[0].endswith("dbip-city-lite-2026-10.mmdb.gz") and asked[1].endswith("dbip-city-lite-2026-09.mmdb.gz")
    assert not list(tmp_path.glob("*.part"))


async def test_a_download_that_does_not_open_never_replaces_the_working_file(tmp_path, monkeypatch):
    (tmp_path / "dbip-city-lite.mmdb").write_bytes(b"good")

    def strict(path):
        if open(path, "rb").read() != b"good":
            raise ValueError("not a database")
        return FakeReader({})
    monkeypatch.setattr(geoip.maxminddb, "open_database", strict)
    client, _ = _server(["2026-10"], body=b"html error page")
    with pytest.raises(ValueError):
        await geoip.refresh(tmp_path, client, now=lambda: NOW)
    assert (tmp_path / "dbip-city-lite.mmdb").read_bytes() == b"good"


async def test_refresh_gives_up_quietly_when_neither_month_exists(tmp_path):
    client, _ = _server([])
    assert await geoip.refresh(tmp_path, client, now=lambda: NOW) is False
    assert not (tmp_path / "dbip-city-lite.mmdb").exists()
