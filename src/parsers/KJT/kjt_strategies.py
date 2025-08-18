import bs4
import os
import regex as re
from typing import Dict, List

from utils import FileUtils
from core.yomitan import create_html_element

from strategies.link import DefaultLinkHandlingStrategy
from strategies.image import HashedImageStrategy

class KJTLinkHandlingStrategy(DefaultLinkHandlingStrategy):
    
    def __init__(self):
        self.appendix_entries = FileUtils.load_json(os.path.join(os.path.dirname(__file__), "mapping/appendix_entries.json"))

    @staticmethod
    def clean_link_text(text: str) -> str:
        text = re.sub(r'[〒〓〈〉《》「」『』【】〔〕〖〗〘〙〚〛〝〞〟()\[\]{}]', '', text)
        return text
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href_val = self.get_href(html_glossary)
        href_val = href_val.replace('index/', 'appendix/')
        if html_glossary.name == "a":
            href = ""
            collected_text = []
            for child in html_glossary.contents:
                if child.name == "mlg":
                    continue
                if isinstance(child, str):  # Plain text
                    collected_text.append(child.strip())
                elif child.name:  # Other elements, preserve their text
                    collected_text.append(child.get_text(strip=True))   
                
            if collected_text:
                href = KJTLinkHandlingStrategy.clean_link_text("".join(filter(None, collected_text)).strip())
                
            if href and not href.isdigit():  # Check that href is not empty and not only digits
                return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
            
        elif href_val.split('#')[0] in self.appendix_entries:
            title = self.appendix_entries[href_val.split('#')[0]]
            link_element = create_html_element("a", content=html_elements, href="?query="+title+"&wildcards=off")
            return create_html_element("span", content=[link_element], data=data_dict)
        
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class KJTImageHandlingStrategy(HashedImageStrategy):

    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, 
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = self.get_src_path(html_glossary)
        if not src_path:
            return create_html_element("span", content=html_elements, data=data_dict)

        if  "img/" in src_path and ".png" in src_path:
            src_path = src_path[:-4] + '.avif'

        if src_path.startswith('../'):
            src_path = src_path.replace('../', '', 1)

        if src_path.startswith("img"):
            src_path = self._get_normalized_filename(src_path)

        img_element = {
            "tag": "img",
            "path": src_path,
            "background": False,
            "collapsed": False,
            "collapsible": False,
            "data": data_dict
        }

        if "筆順" in class_list:
            summary_element = create_html_element("summary", content="筆順")
            return create_html_element("details", content=[summary_element, img_element])
        else:
            html_elements.insert(0, img_element)
            return create_html_element("span", content=html_elements, data=data_dict)