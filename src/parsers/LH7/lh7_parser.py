import os
import bs4
import unicodedata
from typing import Dict, List, Optional

from config import DictionaryConfig
from core.parser_module import YomitanParser
from parsers.Monokakido.utils import MonokakidoUtils
from utils import HTMLUtils
from utils.lang import ExpressionFilter


class LH7Parser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    @staticmethod
    def _preprocess_content(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return HTMLUtils.wrap_example_elements(soup, body_field="body")

    # ----- Utils ----- #
    @staticmethod
    def normalize_text(text: str) -> str:
        decomposed = unicodedata.normalize('NFKD', text)
        filtered = ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')

        return filtered

    @staticmethod
    def extract_text_from_headword(soup: bs4.BeautifulSoup | bs4.PageElement | bs4.Tag | bs4.NavigableString,
                                   entry_keys: List[str] = None, tag: str = "headword") -> Optional[List[str]]:
        headword_tags = soup.find_all(tag)
        if not headword_tags:
            return entry_keys

        if len(entry_keys) > 1:
            return entry_keys

        headwords = []
        for headword_tag in headword_tags:
            texts = []
            for child in headword_tag.children:
                # Entry keys are more reliable if there are brackets in the headword, meaning there are different forms.
                # the keystore always contains all forms.
                if entry_keys and hasattr(child, 'name') and child.name == 'NBracket':
                    return entry_keys

                if hasattr(child, 'name') and child.name in ['rank', 'Hdot', 'Hsup', 'glabel', 'slabel', 'sc', 'img']:
                    continue

                if hasattr(child, 'name') and child.name == 'i':
                    texts = ['£']
                    break

                text = child.get_text(strip=True)
                if text:
                    texts.append(text)

            headwords.append(''.join(texts).replace(",", "").strip())

        return list(set(headwords))

    # ----- Parsing ----- #

    def _parse_idiom_entries(self, soup: bs4.BeautifulSoup, idiom_keys: Dict[str, List[str]]) -> int:
        count = 0
        for subitem in soup.find_all("SubItem"):
            full_id = subitem.get("id")
            item_id = MonokakidoUtils.get_subitem_id(full_id)

            entry_keys = idiom_keys.get(item_id, [])
            if not entry_keys:
                subitem.name = "SubVar"
                continue

            filtered_keys = list(set(ExpressionFilter.filter_substrings(entry_keys)))
            filtered_keys = [key.strip() for key in filtered_keys]
            for key in filtered_keys:
                count += self.parse_entry(key, "", subitem, ignore_expressions=False)

        return count


    def _process_file(self, filename: str, file_content: str) -> int:
        entry_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        idiom_keys = self.idiom_index_reader.get_grouped_entries_for_page(filename_without_ext) if self.idiom_index_reader else None

        soup = bs4.BeautifulSoup(file_content, "xml")
        soup = self._preprocess_content(soup)

        headwords = LH7Parser.extract_text_from_headword(soup, entry_keys, "Headword")
        if len(headwords) == 1:
            headwords = [LH7Parser.normalize_text(headwords[0])]

        if idiom_keys:
            entry_count += self._parse_idiom_entries(soup, idiom_keys)

        for headword in headwords:
            entry_count += self.parse_entry(headword, "", soup, ignore_expressions=True)

        return entry_count
