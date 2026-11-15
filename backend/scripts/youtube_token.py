"""One-time: get the refresh token that lets the worker upload reels to our YouTube channel (app/platform/youtube_upload.py).

Run on a PC with a browser, signed in to the Google account that owns the Avasetu YouTube channel:

    python scripts/youtube_token.py --client-id <id> --client-secret <secret>

The client is an OAuth client of type "Desktop app" in the Google Cloud project that has the YouTube Data API v3 enabled.
The script opens Google's consent page, waits for the answer on http://127.0.0.1:8765, and prints the three lines to add
to the VM's deploy/gcp/.env (with YOUTUBE_UPLOAD=on). Nothing is stored on this PC.
"""
import argparse
import http.server
import secrets
import urllib.parse
import webbrowser

import httpx

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
PORT = 8765
REDIRECT = f"http://127.0.0.1:{PORT}/"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    args = ap.parse_args()
    state = secrets.token_urlsafe(16)
    got: dict = {}

    class Answer(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 (http.server's name)
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            if q.get("state") == state:
                got.update(q)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and go back to the terminal.")

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), Answer)
    url = AUTH + "?" + urllib.parse.urlencode({"client_id": args.client_id, "redirect_uri": REDIRECT, "response_type": "code",
                                               "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening Google's consent page. If it does not open, paste this into the browser:\n" + url)
    webbrowser.open(url)
    server.timeout = 300
    while "code" not in got and "error" not in got:
        server.handle_request()
    if "error" in got:
        raise SystemExit(f"Google said: {got['error']}")
    r = httpx.post(TOKEN, data={"code": got["code"], "client_id": args.client_id, "client_secret": args.client_secret,
                                "redirect_uri": REDIRECT, "grant_type": "authorization_code"}, timeout=30)
    r.raise_for_status()
    refresh = r.json().get("refresh_token")
    if not refresh:
        raise SystemExit("No refresh token came back: remove the app's access at myaccount.google.com/permissions and run again.")
    print("\nAdd these to deploy/gcp/.env on the VM, then redeploy:\n")
    print("YOUTUBE_UPLOAD=on")
    print(f"YOUTUBE_CLIENT_ID={args.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={args.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={refresh}")
    print("YOUTUBE_PRIVACY=private   # until Google's API audit passes; then public")


if __name__ == "__main__":
    main()
