import bs4

from utils.lang import KanjiUtils
from parsers.Monokakido.parser import MonokakidoParser
from config import DictionaryConfig


class SKOGOParser(MonokakidoParser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    @staticmethod
    def extract_guide_entry(soup):
        """Extracts 識別 entries in the guide entries that dont have any keys."""
        # E.g しかの識別
        reading = ""

        head_element = soup.find("識別見出行")
        if head_element:
            reading_element = head_element.find("識別見出")
            if reading_element:
                reading = reading_element.text.strip()

            sub_element = head_element.find("識別見出サブ")
            if sub_element:
                guide_type = sub_element.text.strip()
                entry_key = reading + guide_type
                return KanjiUtils.clean_headword(entry_key)

        return ""

    def _parse_entries_from_html(self, soup: bs4.BeautifulSoup) -> int:
        count = 0

        head_word, reading = self.normalization_strategy.extract_rekishi_gendai(soup)
        if reading:
            count += self.parse_entry(head_word, reading, soup)

        guide_entry = SKOGOParser.extract_guide_entry(soup)
        if guide_entry:
            count += self.parse_entry(guide_entry, "", soup)

        return count