from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict

import pytest

from grogbot_search.service import SearchService


@pytest.fixture()
def service(tmp_path, monkeypatch):
    def fake_embed(texts, *, prompt):
        return [[0.0] * 768 for _ in texts]

    monkeypatch.setattr("grogbot_search.service.embed_texts", fake_embed)
    db_path = tmp_path / "search.db"
    svc = SearchService(db_path)
    yield svc
    svc.close()


@pytest.fixture()
def http_server():
    responses: Dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = responses.get(self.path)
            if body is None:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            if "opml" in self.path:
                self.send_header("Content-Type", "text/x-opml+xml")
            elif "sitemap" in self.path or self.path.endswith(".xml") or "rss" in self.path:
                self.send_header("Content-Type", "application/xml")
            else:
                self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, format, *args):  # noqa: A003 - match base signature
            return

    server = ThreadingHTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://localhost:{server.server_address[1]}"

    responses["/article"] = f"""
    <html>
      <head>
        <title>Test Article</title>
        <link rel=\"canonical\" href=\"{base_url}/canonical\" />
      </head>
      <body>
        <article>
          <h1>Article Heading</h1>
          <p>Hello world from article content.</p>
        </article>
      </body>
    </html>
    """

    responses["/article-2"] = f"""
    <html>
      <head>
        <title>Second Test Article</title>
        <link rel="canonical" href="{base_url}/canonical-2" />
      </head>
      <body>
        <article>
          <h1>Second Article Heading</h1>
          <p>Hello world from second article content.</p>
        </article>
      </body>
    </html>
    """

    responses["/feed"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>Test Feed</title>
        <item>
          <title>Feed Entry</title>
          <link>{base_url}/feed-entry</link>
          <guid>{base_url}/feed-entry</guid>
          <content:encoded><![CDATA[<p>Feed body content.</p>]]></content:encoded>
          <pubDate>Wed, 01 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/feed2"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>Test Feed 2</title>
        <item>
          <title>Second Feed Entry</title>
          <link>{base_url}/feed2-entry</link>
          <guid>{base_url}/feed2-entry</guid>
          <content:encoded><![CDATA[<p>Second feed body content.</p>]]></content:encoded>
          <pubDate>Thu, 02 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/invalid-feed"] = "NOT VALID XML"

    responses["/opml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <opml version="2.0">
      <head>
        <title>Test Subscriptions</title>
      </head>
      <body>
        <outline text="Test Feed" type="rss" xmlUrl="{base_url}/feed" />
        <outline text="Test Feed 2" type="rss" xmlUrl="{base_url}/feed2" />
      </body>
    </opml>
    """

    responses["/opml-nested"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <opml version="2.0">
      <head>
        <title>Nested Subscriptions</title>
      </head>
      <body>
        <outline text="Category 1">
          <outline text="Test Feed" type="rss" xmlUrl="{base_url}/feed" />
          <outline text="Invalid" type="rss" xmlUrl="{base_url}/invalid-feed" />
        </outline>
        <outline text="Category 2">
          <outline text="Test Feed 2" type="rss" xmlUrl="{base_url}/feed2" />
        </outline>
      </body>
    </opml>
    """

    responses["/opml-duplicates"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <opml version="2.0">
      <head>
        <title>Duplicate Subscriptions</title>
      </head>
      <body>
        <outline text="Test Feed" type="rss" xmlUrl="{base_url}/feed" />
        <outline text="Same Feed Again" type="rss" xmlUrl="{base_url}/feed" />
      </body>
    </opml>
    """

    responses["/sitemap.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>{base_url}/article</loc>
      </url>
      <url>
        <loc>{base_url}/article-2</loc>
      </url>
      <url>
        <loc>{base_url}/missing</loc>
      </url>
    </urlset>
    """

    responses["/sitemap-duplicates.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/article</loc></url>
      <url><loc>{base_url}/article</loc></url>
    </urlset>
    """

    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join()
