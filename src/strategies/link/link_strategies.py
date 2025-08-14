import bs4
from abc import ABC, abstractmethod
from typing import Dict, List

from core.yomitan import create_html_element


class LinkHandlingStrategy(ABC):
    @abstractmethod
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        pass

    @abstractmethod
    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        pass
        
        
class DefaultLinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href = self.get_href(html_glossary)
            
        if href and not href.isdigit():  # Check that href is not empty and not only digits
            return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
    
        return create_html_element("span", content=html_elements, data=data_dict)

    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        return html_glossary.text.strip()