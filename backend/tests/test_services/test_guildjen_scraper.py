"""Tests for GuildJenScraper."""

from bs4 import BeautifulSoup

from app.services.scraper.guildjen_scraper import GuildJenScraper


def test_extract_chat_code_from_chat_code_input():
    """GuildJenScraper should find a GW2 chat code from a chat-code input field."""

    html = """
    <html>
      <body>
        <input type="text" class="chat-code" value="[&DQYfFR0mAAAA]" />
      </body>
    </html>
    """

    scraper = GuildJenScraper()
    soup = BeautifulSoup(html, "html.parser")

    chat_code = scraper._extract_chat_code(soup, html)

    assert chat_code == "[&DQYfFR0mAAAA]"
