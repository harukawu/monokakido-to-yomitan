import bs4
import re
import unicodedata
from typing import List, Dict

from core.yomitan import create_html_element
from strategies.link import DefaultLinkHandlingStrategy


class LH7LinkHandlingStrategy(DefaultLinkHandlingStrategy):
    def __init__(self) -> None:
        self.valid_href = re.compile(r'^(\d+|\d+-4\d+|\d+-8\d+)$')

    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href = self.get_href(html_glossary)
        if not href:
            return create_html_element("span", content=html_elements, data=data_dict)

        href_val = html_glossary.get("href", "")
        if not self.valid_href.match(href_val):
            return create_html_element("span", content=html_elements, data=data_dict)

        texts = []
        for child in html_glossary.children:
            if hasattr(child, 'name') and child.name in ['rank', 'Hdot', 'Hsup', 'glabel', 'slabel', 'sup', 'img']:
                continue

            text = child.get_text(strip=True)
            texts.append(text)

        processed_href = ''.join(texts)
        decomposed = unicodedata.normalize('NFKD', processed_href)
        new_href = ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')
        return create_html_element("a", content=html_elements, href=f"?query={new_href}&wildcards=off")


    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        href = html_glossary.text.strip()
        if not href or href.isdigit():
            return ""

        return href