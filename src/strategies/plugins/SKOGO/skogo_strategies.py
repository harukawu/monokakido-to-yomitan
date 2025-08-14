import regex as re
import bs4
import jaconv
from typing import Tuple

from utils import HTMLUtils
from utils.lang import KanjiUtils
from strategies.link import DefaultLinkHandlingStrategy
from strategies.normalization import DefaultNormalizationStrategy

class SKOGOLinkHandlingStrategy(DefaultLinkHandlingStrategy):

    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        if html_glossary.text and "識別" in html_glossary.text:
            guide_ref = KanjiUtils.clean_headword(html_glossary.text.strip())
            return guide_ref

        if not "blue" in html_glossary.get("class", bs4.element.AttributeValueList()):
            return ""

        href = ""

        # Check for 表記G first
        hyoki_g = html_glossary.find('表記G')
        if hyoki_g:
            href = hyoki_g.text.strip()

            if any(KanjiUtils.is_kanji(c) for c in href):
                href = KanjiUtils.clean_headword(href).split('・')[0]
            else:
                href = re.sub("・", "", href)

        if not href:
            midashi_g = html_glossary.find('見出G')
            if midashi_g:
                href = KanjiUtils.clean_reading(midashi_g.text.strip())

        return href


class SKOGONormalizationStrategy(DefaultNormalizationStrategy):
    @staticmethod
    def extract_gendai_reading(soup):
        # Attempt to find a reading in the Head element
        head_element = soup.find("見出部")
        if head_element:
            element = head_element.find("Gendai見出")
            if element:
                reading = element.text.strip()
                return KanjiUtils.clean_reading(reading)

        return ""

    @staticmethod
    def extract_rekishi_gendai(soup) -> Tuple[str, str]:
        head_word = ""
        reading = ""

        # Attempt to find a reading in the Head element
        head_element = soup.find("見出部")
        if head_element:
            head_word_element = head_element.find("見出G")
            if head_word_element:
                head_word = head_word_element.text.strip()
                head_word = jaconv.kata2hira(KanjiUtils.clean_headword(head_word))

            reading_element = head_element.find("見出現代仮名")
            if reading_element:
                reading = reading_element.text.strip()
                reading = jaconv.kata2hira(KanjiUtils.clean_reading(reading))
            else:
                return "", ""

        return head_word, reading


    def get_context(self, soup: bs4.BeautifulSoup) -> str:
        reading = HTMLUtils.extract_field(soup, "見出G")

        # No reading found, try 現代 entry (e.g のたまう entry with link to のたまふ)
        if not reading:
            reading = SKOGONormalizationStrategy.extract_gendai_reading(soup)

        # No reading found, try 歴史現代 reading and
        if not reading:
            # Parse these entries as specific case
            _, reading = SKOGONormalizationStrategy.extract_rekishi_gendai(soup)

        return reading
