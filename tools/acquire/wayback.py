"""Small Wayback Machine client: polite, retrying, standard library only."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import config


class WaybackError(Exception):
    pass


def _looks_offline(body):
    head = body[:600].lower()
    return b'<html' in head and (b'temporarily offline' in head or b'service unavailable' in head)


def get(url):
    """GET with a pause before each request and exponential backoff on failures."""
    last = None
    for attempt in range(config.RETRIES):
        time.sleep(config.DELAY_SECONDS * (2 ** attempt if attempt else 1))
        req = urllib.request.Request(url, headers={'User-Agent': config.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=config.TIMEOUT_SECONDS) as r:
                body = r.read()
            if _looks_offline(body):
                last = 'archive reported it was temporarily offline'
                continue
            return body
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = repr(e)
    raise WaybackError('giving up on %s after %d attempts: %s' % (url, config.RETRIES, last))


def cdx(pattern):
    """All index rows matching a URL pattern. Returns (header, rows)."""
    qs = urllib.parse.urlencode({'url': pattern, 'output': 'json', 'fl': config.CDX_FIELDS,
                                 'limit': config.CDX_LIMIT})
    body = get('https://web.archive.org/cdx/search/cdx?' + qs)
    if not body.strip():
        return config.CDX_FIELDS.split(','), []
    data = json.loads(body)
    return data[0], data[1:]


def fetch_capture(timestamp, original):
    """Fetch the bytes of one capture exactly as stored ('id_' avoids archive rewriting)."""
    return get('https://web.archive.org/web/%sid_/%s' % (timestamp, original))
