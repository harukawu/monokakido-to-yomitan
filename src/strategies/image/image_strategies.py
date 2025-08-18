import os
import bs4
from abc import ABC, abstractmethod
from typing import Dict, List

from core.yomitan import create_html_element


class ImageHandlingStrategy(ABC):
    @abstractmethod
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        pass

    @abstractmethod
    def get_src_path(self, html_glossary: bs4.element.Tag) -> str:
        pass
    
    
class DefaultImageHandlingStrategy(ImageHandlingStrategy):
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = self.get_src_path(html_glossary)
        if src_path:
            image_element = {
                "tag": "img", 
                "path": src_path,
                "background": False,
                "collapsed": False,
                "collapsible": False,
                "data": data_dict
            }
            html_elements.insert(0, image_element)
        
        return create_html_element("span", content=html_elements, data=data_dict)

    def get_src_path(self, html_glossary: bs4.element.Tag) -> str:
        return html_glossary.get("src", "").lstrip("/")


class GaijiImageHandlingStrategy(DefaultImageHandlingStrategy):
    @abstractmethod
    def __init__(self):
        self.replacements = {}

    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = self.get_src_path(html_glossary)
        if not src_path:
            return create_html_element("span", content=html_elements, data=data_dict)

        basename = os.path.basename(src_path)
        if basename in self.replacements:
            text = self.replacements[basename]["text"]
            class_name = self.replacements[basename]["class"]
            data_dict[class_name] = ""
            return create_html_element("span", content=text, data=data_dict)
        else:
            imgElement = {
                "tag": "img",
                "path": src_path,
                "background": False,
                "collapsed": False,
                "collapsible": False,
                "data": data_dict
            }
            html_elements.insert(0, imgElement)
            return create_html_element("span", content=html_elements, data=data_dict)