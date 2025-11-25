"""Tests for HardstuckScraper."""

from bs4 import BeautifulSoup

from app.services.scraper.hardstuck_scraper import HardstuckScraper


def test_extract_chat_code_from_input_value():
    """HardstuckScraper should find a GW2 chat code from an input value attribute."""

    html = """
    <html>
      <body>
        <input type="text" readonly value="[&DQYfFR0mAAAA]" />
      </body>
    </html>
    """

    scraper = HardstuckScraper()
    soup = BeautifulSoup(html, "html.parser")

    chat_code = scraper._extract_chat_code(soup, html)

    assert chat_code == "[&DQYfFR0mAAAA]"
