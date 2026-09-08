"""Smoke-test the seeded local demo through real authenticated HTTP requests.

Run after seed_demo.py and `docker compose up -d odoo`.
Uses only Python's standard library and a separate demo login session.
"""

from http.cookiejar import CookieJar
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


BASE_URL = "http://localhost:8079"
expected_bytes = (Path(__file__).resolve().parents[1] / "output/pdf/kitchen_measurement.pdf").read_bytes()


def rpc(opener, endpoint, params):
    request = Request(
        BASE_URL + endpoint,
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params, "id": 1}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with opener.open(request, timeout=30) as response:
        result = json.load(response)
    if "error" in result:
        raise AssertionError(result["error"])
    return result["result"]


def search_read(opener, model, domain, fields):
    return rpc(
        opener,
        f"/web/dataset/call_kw/{model}/search_read",
        {"model": model, "method": "search_read", "args": [domain], "kwargs": {"fields": fields}},
    )


for login, password in (("admin", "furniture-demo"), ("workshop", "workshop-demo")):
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    result = rpc(
        opener,
        "/web/session/authenticate",
        {"db": "furniture_demo", "login": login, "password": password},
    )
    assert result["uid"], "Authentication failed"
    orders = search_read(
        opener,
        "sale.order",
        [("client_order_ref", "=", "FURNITURE-DEMO-001")],
        ["order_line", "production_address", "attachment_name"],
    )
    assert len(orders) == 1
    productions = search_read(
        opener,
        "mrp.production",
        [("sale_line_id", "in", orders[0]["order_line"])],
        ["production_address", "attachment_name"],
    )
    assert len(productions) == 1
    production = productions[0]
    assert production["production_address"] == "Sho'rchi, Shaldiroq MFY"
    assert production["attachment_name"] == "kitchen_measurement.pdf"
    download_url = BASE_URL + "/web/content?" + urlencode(
        {
            "model": "mrp.production",
            "id": production["id"],
            "field": "order_attachment",
            "filename_field": "attachment_name",
            "download": "true",
        }
    )
    with opener.open(download_url, timeout=30) as response:
        assert response.status == 200
        assert "kitchen_measurement.pdf" in response.headers["Content-Disposition"]
        assert response.read() == expected_bytes, "Downloaded PDF differs from source"
    print(f"PASS: {login} reads the MO and downloads the exact PDF with its filename.")

try:
    with build_opener().open(download_url, timeout=30) as response:
        assert response.read() != expected_bytes, "Anonymous access exposed the drawing"
except HTTPError as error:
    assert error.code in (401, 403, 404)
print("PASS: anonymous request cannot download the drawing.")
