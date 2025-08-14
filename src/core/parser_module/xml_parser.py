from typing import List, Dict, Optional, Tuple
import bs4

from .base_parser import BaseParser
from config import DictionaryConfig
from utils import FileUtils


class XMLParser(BaseParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

        from core import HTMLToYomitanConverter
        from index import IndexReader, JukugoIndexReader
        from handlers import ManualMatchHandler

        self.index_reader = IndexReader(config.index_path) if config.index_path else None
        self.jukugo_index_reader = JukugoIndexReader(config.jukugo_index_path) if config.jukugo_index_path else None
        self.idiom_index_reader = JukugoIndexReader(config.idiom_index_path) if config.idiom_index_path else None
        self.kanji_index_reader = IndexReader(config.kanji_index_path) if config.kanji_index_path else None

        self.tag_mapping = FileUtils.load_json(config.tag_map_path) if config.tag_map_path else {}
        self.manual_handler = ManualMatchHandler() if config.index_path else None

        self.link_handling_strategy = config.create_link_strategy()
        self.image_handling_strategy = config.create_image_strategy()
        self.pos_tag_strategy = config.create_pos_tags_strategy()

        self.html_converter = HTMLToYomitanConverter(
            tag_mapping=self.tag_mapping,
            ignored_elements=config.ignored_elements,
            expression_element=config.expression_element,
            link_handling_strategy=self.link_handling_strategy,
            image_handling_strategy=self.image_handling_strategy,
            parse_all_links=config.parse_all_links
        )

        self.bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"


    def get_target_tag(self, tag_name: str, class_list: Optional[List[str]] = None,
                       parent: Optional[bs4.element.Tag] = None, recursion_depth: int = 0) -> str:
        """
        Get the appropriate HTML tag based on tag name and CSS classes
        """
        return self.html_converter.get_target_tag(tag_name, class_list, parent, recursion_depth)


    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        return self.html_converter.handle_link_element(html_glossary, html_elements, data_dict, class_list)


    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, data_dict: Dict,
                             class_list: List[str]) -> str:
        return self.html_converter.handle_image_element(html_glossary, html_elements, data_dict, class_list)


    def get_class_list_and_data(self, html_glossary: bs4.element.Tag) -> Tuple[List[str], Dict[str, str]]:
        """Extract class list and data attributes from an HTML element"""
        return self.html_converter.get_class_list_and_data(html_glossary)


    def convert_element_to_yomitan(self, html_glossary: Optional[bs4.element.Tag] = None,
                                   ignore_expressions: bool = False) -> Optional[Dict]:
        """Recursively converts HTML elements into Yomitan JSON format"""
        return self.html_converter.convert_element_to_yomitan(
            html_glossary, ignore_expressions
        )