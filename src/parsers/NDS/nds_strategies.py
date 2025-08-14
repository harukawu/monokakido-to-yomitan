import bs4
import re
from typing import List, Dict

from core.yomitan import create_html_element
from strategies.link import DefaultLinkHandlingStrategy


class NDSLinkHandlingStrategy(DefaultLinkHandlingStrategy):

    def __init__(self):
        self.subitem_regex = re.compile(r'(\d+)-(4)([0-9a-fA-F]+)')

    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:

        href_val = html_glossary.get("href", "")
        element_text_content = html_glossary.get_text(strip=True).strip()
        element_class = html_glossary.get("class", "")

        if 'n' in element_class:
            if href_val.isdigit() or href_val.replace("-", "").isdigit():
                print(f"break")

            return create_html_element("span", content=html_elements, data=data_dict)


        if href_val.isdigit() and element_text_content:
            return create_html_element("a", content=html_elements, href="?query=" + element_text_content + "&wildcards=off")

        subitem_match = re.match(self.subitem_regex, href_val)
        if subitem_match and element_text_content:
            return create_html_element("a", content=html_elements, href="?query=" + element_text_content + "&wildcards=off")


        return create_html_element("a", content=html_elements, href="?query=" + element_text_content + "&wildcards=off")