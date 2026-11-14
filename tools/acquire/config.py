"""Configuration for the COF archive lister. Environment variables override the defaults."""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

# Where raw index responses, cached listing pages and the manifest are written.
OUT_DIR = os.environ.get('ACQUIRE_OUT') or os.path.join(_ROOT, 'data', 'acquire')

# Politeness / robustness for requests to web.archive.org.
DELAY_SECONDS = float(os.environ.get('WAYBACK_DELAY', '2.0'))   # pause before every request
RETRIES = int(os.environ.get('WAYBACK_RETRIES', '5'))
TIMEOUT_SECONDS = int(os.environ.get('WAYBACK_TIMEOUT', '120'))
USER_AGENT = 'cof-archive-lister/0.1 (personal research; index queries)'

# CDX prefix queries, one per URL era / host. Name -> url pattern.
PATTERNS = {
    'era12_previewsworld': 'previewsworld.com/support/previews_docs/orderforms/*',
    'era12_diamondcomics': 'diamondcomics.com/support/previews_docs/orderforms/*',
    'era3_txt': 'previewsworld.com/Catalog/CustomerOrderForm/TXT/*',
    'era3_pdf': 'previewsworld.com/Catalog/CustomerOrderForm/PDF/*',
}
CDX_LIMIT = 100000
CDX_FIELDS = 'timestamp,original,statuscode,mimetype,length,digest'

# The listing page that linked recent forms.
LISTING_URL = 'previewsworld.com/Catalog/CustomerOrderForms'
LISTING_EVERY_DAYS = int(os.environ.get('LISTING_EVERY_DAYS', '90'))   # sample one capture per N days

# A capture is "plausible" when status 200, the expected MIME type, and at least this many bytes.
PLAUSIBLE = {'txt': ('text/plain', 5000), 'pdf': ('application/pdf', 100000)}

# Months the report expects to find.
EXPECT_FROM = 'JAN09'
EXPECT_TO = 'DEC25'
