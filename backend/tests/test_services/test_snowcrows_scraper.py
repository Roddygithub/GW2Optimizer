"""Tests for SnowcrowsScraper."""

from bs4 import BeautifulSoup

from app.services.scraper.snowcrows_scraper import SnowcrowsScraper


def test_extract_chat_code_from_html_snippet():
    """SnowcrowsScraper should find a GW2 chat code in a typical HTML snippet."""

    html = """
    <html>
      <body>
        <button data-clipboard-text="[&DQYfFR0mAAAA]">Copy Chat Code</button>
      </body>
    </html>
    """

    scraper = SnowcrowsScraper()
    soup = BeautifulSoup(html, "html.parser")

    chat_code = scraper._extract_chat_code(soup, html)

    assert chat_code == "[&DQYfFR0mAAAA]"
