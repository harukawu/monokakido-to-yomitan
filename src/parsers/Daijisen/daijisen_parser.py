import bs4

from parsers.Monokakido.parser import MonokakidoParser
from core.yomitan import DicEntry
from config import DictionaryConfig
from parsers.DAIJISEN.daijisen_utils import DaijisenUtils


class DaijisenParser(MonokakidoParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    def _handle_plus_entries(self, soup: bs4.BeautifulSoup) -> int:
        if not soup.find("Header", class_="DJSP"):
            return 0

        count = 0
        plus_terms = DaijisenUtils.extract_plus_headword(soup)
        for term in plus_terms:
            info_tag, pos_tag = self.pos_tag_strategy.get_from_term(term)
            count += self.parse_entry(term, "", soup, pos_tag=pos_tag, search_rank=-1, ignore_expressions=True)

        return count

    def _handle_expression_entries(self, soup: bs4.BeautifulSoup):
        count = 0

        for sub_item in soup.find_all(self.config.expression_element):
            headword_element = sub_item.find("headword", class_="見出")
            expression, readings = DaijisenUtils.extract_wari_text(headword_element)
            _, pos_tag = self.pos_tag_strategy.get_from_term(expression)

            if readings:
                for reading in readings:
                    entry = DicEntry(expression, reading, info_tag="", pos_tag=pos_tag)
                    yomitan_element = self.convert_element_to_yomitan(sub_item, ignore_expressions=False)
                    if yomitan_element:
                        entry.add_element(yomitan_element)

                    self.dictionary.add_entry(entry)
                    count += 1

            else:
                entry = DicEntry(expression, "", info_tag="", pos_tag=pos_tag)
                yomitan_element = self.convert_element_to_yomitan(sub_item, ignore_expressions=False)
                if yomitan_element:
                    entry.add_element(yomitan_element)

                self.dictionary.add_entry(entry)
                count += 1

        return count

    def _parse_entries_from_html(self, soup: bs4.BeautifulSoup) -> int:
        count = 0

        count += self._handle_expression_entries(soup)

        count += self._handle_plus_entries(soup)

        return count
