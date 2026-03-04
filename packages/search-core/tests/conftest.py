from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

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
    responses: Dict[str, str | Dict[str, Any]] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            response = responses.get(self.path)
            if response is None:
                self.send_response(404)
                self.end_headers()
                return

            if isinstance(response, str):
                body = response
                status_code = 200
                headers: Dict[str, str] = {}
            else:
                body = str(response.get("body", ""))
                status_code = int(response.get("status", 200))
                raw_headers = response.get("headers") or {}
                headers = {str(k): str(v) for k, v in dict(raw_headers).items()}

            self.send_response(status_code)
            content_type = headers.pop("Content-Type", None)
            if content_type is None:
                if "opml" in self.path:
                    content_type = "text/x-opml+xml"
                elif "sitemap" in self.path or self.path.endswith(".xml") or "rss" in self.path:
                    content_type = "application/xml"
                else:
                    content_type = "text/html"
            self.send_header("Content-Type", content_type)
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
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

    responses["/feed-paginated"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>Paginated Feed</title>
        <atom:link rel="next" href="{base_url}/feed-paginated-2" />
        <item>
          <title>Paginated Entry 1</title>
          <link>{base_url}/feed-paginated-entry-1</link>
          <guid>{base_url}/feed-paginated-entry-1</guid>
          <content:encoded><![CDATA[<p>Paginated entry one.</p>]]></content:encoded>
          <pubDate>Fri, 03 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/feed-paginated-2"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>Paginated Feed</title>
        <item>
          <title>Paginated Entry 2</title>
          <link>{base_url}/feed-paginated-entry-2</link>
          <guid>{base_url}/feed-paginated-entry-2</guid>
          <content:encoded><![CDATA[<p>Paginated entry two.</p>]]></content:encoded>
          <pubDate>Sat, 04 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/wp-feed"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>WordPress Feed</title>
        <generator>WordPress</generator>
        <item>
          <title>WordPress Entry 1</title>
          <link>{base_url}/wp-feed-entry-1</link>
          <guid>{base_url}/wp-feed-entry-1</guid>
          <content:encoded><![CDATA[<p>WordPress entry one.</p>]]></content:encoded>
          <pubDate>Sun, 07 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/wp-feed?paged=2"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>WordPress Feed</title>
        <generator>WordPress</generator>
        <item>
          <title>WordPress Entry 2</title>
          <link>{base_url}/wp-feed-entry-2</link>
          <guid>{base_url}/wp-feed-entry-2</guid>
          <content:encoded><![CDATA[<p>WordPress entry two.</p>]]></content:encoded>
          <pubDate>Mon, 08 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/feed-loop"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>Loop Feed</title>
        <atom:link rel="next" href="{base_url}/feed-loop" />
        <item>
          <title>Loop Entry</title>
          <link>{base_url}/feed-loop-entry</link>
          <guid>{base_url}/feed-loop-entry</guid>
          <content:encoded><![CDATA[<p>Loop entry.</p>]]></content:encoded>
          <pubDate>Sun, 05 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/feed-paginated-error"] = f"""
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>Error Feed</title>
        <atom:link rel="next" href="{base_url}/feed-paginated-error-2" />
        <item>
          <title>Error Entry</title>
          <link>{base_url}/feed-paginated-error-entry</link>
          <guid>{base_url}/feed-paginated-error-entry</guid>
          <content:encoded><![CDATA[<p>Error entry.</p>]]></content:encoded>
          <pubDate>Mon, 06 Jan 2025 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    responses["/feed-paginated-error-2"] = {
        "status": 500,
        "body": "Server error",
    }

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

    responses["/backoff-403"] = {
        "status": 403,
        "body": "Forbidden",
    }
    responses["/backoff-429"] = {
        "status": 429,
        "body": "Too Many Requests",
    }
    responses["/backoff-503"] = {
        "status": 503,
        "body": "Service Unavailable",
    }
    responses["/backoff-retry-after"] = {
        "status": 200,
        "headers": {"Retry-After": "120"},
        "body": "Please slow down",
    }
    responses["/backoff-captcha"] = {
        "status": 200,
        "body": """
        <html>
          <head><title>Attention Required</title></head>
          <body>Please verify you are human (captcha challenge)</body>
        </html>
        """,
    }

    responses["/sitemap-backoff-403.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/article</loc></url>
      <url><loc>{base_url}/backoff-403</loc></url>
      <url><loc>{base_url}/article-2</loc></url>
    </urlset>
    """

    responses["/sitemap-backoff-429.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/backoff-429</loc></url>
    </urlset>
    """

    responses["/sitemap-backoff-503.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/backoff-503</loc></url>
    </urlset>
    """

    responses["/sitemap-backoff-retry-after.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/backoff-retry-after</loc></url>
    </urlset>
    """

    responses["/sitemap-backoff-captcha.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{base_url}/backoff-captcha</loc></url>
    </urlset>
    """

    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join()
