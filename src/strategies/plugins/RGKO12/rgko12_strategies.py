import os
import bs4
from pathlib import Path
from typing import Dict, List

from core.yomitan import create_html_element
from strategies.image import HashedImageStrategy
from strategies.link import DefaultLinkHandlingStrategy
from utils import FileUtils, HTMLUtils


class RGKO12LinkHandlingStrategy(DefaultLinkHandlingStrategy):

    def __init__(self):
        self.appendix_entries = FileUtils.load_json(
            str(Path(__file__).parent.parent.parent.parent.parent / "resources/RGKO12/mapping/appendix_entries.json")
        )

    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        href = html_glossary.get("href", "")
        if href.split('#')[0] in self.appendix_entries:
            return self.appendix_entries[href.split('#')[0]]

        if html_glossary.find("ruby"):
            return HTMLUtils.extract_ruby_text(html_glossary)

        if html_glossary.text:
            return html_glossary.text.strip()

        return ""


class RGKO12ImageHandlingStrategy(HashedImageStrategy):

    def __init__(self, image_map_path: str) -> None:
        super().__init__(image_map_path)
        self.missing_images = {
            "名・形動とたる.svg",
            "形動とたる.svg"
        }

        self.base_path = Path(__file__).parent.parent.parent.parent.parent
        self.gaiji_replacements = FileUtils.load_json(
            str(self.base_path / "resources/RGKO12/mapping/gaiji_replacements.json")
        )

    @staticmethod
    def set_class_names(class_: str, data: Dict) -> Dict:
        class_list = class_.split(' ')
        for class_ in class_list:
            data[class_] = ""
        return data

    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        basename = os.path.basename(src_path)

        if not src_path or basename in self.missing_images:
            return create_html_element("span", content=html_elements, data=data_dict)

        if src_path.startswith('../'):
            src_path = src_path.replace('../', '', 1)

        if basename in self.gaiji_replacements:
            # Get replacements
            text = self.gaiji_replacements[basename]["text"]
            class_name = self.gaiji_replacements[basename]["class"]

            # Update data attributes
            data_dict = RGKO12ImageHandlingStrategy.set_class_names(class_name, data_dict)

            return create_html_element("span", content=text, data=data_dict)
        else:
            hashed_filename = self._get_normalized_filename(src_path)
            if hashed_filename.lower().endswith('.png'):
                hashed_filename = hashed_filename[:-4] + '.avif'

            img_element = {
                "tag": "img",
                "path": hashed_filename,
                "background": False,
                "data": data_dict
            }

            if "hitsujun" in src_path.lower():
                summary_element = create_html_element("summary", content="筆順")
                return create_html_element("details", content=[summary_element, img_element])
            else:
                html_elements.insert(0, img_element)

            return create_html_element("span", content=html_elements, data=data_dict)
