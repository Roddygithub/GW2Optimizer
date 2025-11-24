"""Tests for GW2MistsScraper."""

from bs4 import BeautifulSoup

from app.services.scraper.gw2mists_scraper import GW2MistsScraper


def test_extract_chat_code_from_script_json():
    """GW2MistsScraper should find a GW2 chat code inside script JSON."""

    html = """
    <html>
      <body>
        <script type="application/json">
          {"build": {"chat_code": "[&DQYfFR0mAAAA]"}}
        </script>
      </body>
    </html>
    """

    scraper = GW2MistsScraper()
    soup = BeautifulSoup(html, "html.parser")

    chat_code = scraper._extract_chat_code(soup, html)

    assert chat_code == "[&DQYfFR0mAAAA]"
