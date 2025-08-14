import regex as re
import bs4
from typing import Dict, List

from core.yomitan import create_html_element
from strategies.link import DefaultLinkHandlingStrategy
from strategies.image import DefaultImageHandlingStrategy

class CJ3LinkHandlingStrategy(DefaultLinkHandlingStrategy):
	def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
							data_dict: Dict, class_list: List[str]) -> Dict:
		href = self.get_href(html_glossary)
		
		if href and not href.isdigit():
			href = re.sub(r'\[', '', href)
			href = re.sub(r'\]', '', href)
			href = re.sub(r"[\p{Block=CJK_Symbols_and_Punctuation}]", '', href)
			return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
	
		return create_html_element("span", content=html_elements, data=data_dict)
	
	
class CJ3ImageHandlingStrategy(DefaultImageHandlingStrategy):
	def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
							data_dict: Dict, class_list: List[str]) -> Dict:
		src_path = self.get_src_path(html_glossary)
		if src_path and src_path != "HMDicAudio.png":
			if not src_path.startswith("gaiji") and src_path.endswith(".png"):
				src_path = src_path[:-4] + '.avif'
			
			img_element = {
				"tag": "img", 
				"path": src_path,
				"background": False,
				"data": data_dict
			}
			html_elements.insert(0, img_element)
			
		return create_html_element("span", content=html_elements, data=data_dict)