import os
import re
import bs4
import jaconv
from typing import List

from config import DictionaryConfig
from core.parser_module import YomitanParser
from parsers.Monokakido.utils import MonokakidoUtils
from utils import HTMLUtils

from handlers import process_unmatched_entries
from utils.lang import ExpressionFilter, KanjiUtils


class MonokakidoParser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    def _parse_entries_from_html(self, soup: bs4.BeautifulSoup) -> int:
        """Can be implemented to extract any additional entries directly from the html content.
           E.g if there are entries that aren't included in the keystore files"""
        return 0

    def _preprocess_content(self, soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return soup

    def _process_file(self, filename: str, file_content: str) -> int:
        entry_count = 0
        filename_without_ext = os.path.splitext(filename)[0]

        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        kanji_keys = list(
            set(self.kanji_index_reader.get_keys_for_file(filename_without_ext))) if self.kanji_index_reader else None
        idiom_keys = self.idiom_index_reader.get_organized_entries_for_page(
            filename_without_ext) if self.idiom_index_reader else None

        # Parse xml
        soup = bs4.BeautifulSoup(file_content, "xml")
        soup = self._preprocess_content(soup)

        if entry_keys:
            entry_count += self._parse_head_entries(soup, entry_keys, filename)

        if kanji_keys:
            entry_count += self._parse_kanji_entries(soup, kanji_keys)

        if idiom_keys:
            entry_count += self._parse_idiom_entries(soup, idiom_keys)

        entry_count += self._parse_entries_from_html(soup)

        return entry_count

    def _parse_head_entries(self, soup: bs4.BeautifulSoup, entry_keys: List[str], filename: str) -> int:
        count = 0

        # Normalise and match keys
        normalized_keys = self.normalization_strategy.normalize_keys(entry_keys, soup)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, normalized_keys, matched_key_pairs, self.manual_handler
        )

        # Process each key pair
        added_usually_kana = set()
        for kanji_part, kana_part in matched_key_pairs:
            pos_tag = ""
            if kanji_part:
                info_tag, pos_tag = self.pos_tag_strategy.get_from_term(kanji_part)
                count += self.parse_entry(
                    kanji_part, kana_part, soup, pos_tag=pos_tag
                )

                if "uk" in info_tag and kana_part not in added_usually_kana:
                    count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag)
                    added_usually_kana.add(kana_part)

            elif kana_part and kana_part not in added_usually_kana:
                count += self.parse_entry(
                    kana_part, "", soup, pos_tag=pos_tag
                )

        return count

    def _parse_kanji_entries(self, soup: bs4.BeautifulSoup, entry_keys: List[str]) -> int:
        count = 0

        kanji_keys = [k for k in entry_keys if any(KanjiUtils.is_kanji(c) for c in k)]
        reading_keys = [k for k in entry_keys if k not in kanji_keys and k != '〓']

        for kanji in kanji_keys:
            if sum(KanjiUtils.is_kanji(c) for c in kanji) > 1:
                print(f"Found compound in kanji keystore: {kanji}, keys: {entry_keys}")
                continue

            for reading in reading_keys:
                reading = jaconv.kata2hira(reading)
                count += self.parse_entry(kanji, reading, soup, ignore_expressions=True)

        return count

    def _parse_idiom_entries(self, soup: bs4.BeautifulSoup, idiom_keys: dict) -> int:
        count = 0

        if len(idiom_keys) > 1 and self.config.subitems_not_split:
            print(f"\nFound more than one idiom entry in unsplit dictionary: {idiom_keys}")

        if len(idiom_keys) == 1 and self.config.subitems_not_split:
            return self._parse_non_split_idiom_entry(soup, idiom_keys)

        for subitem in soup.find_all(self.config.expression_element, re.IGNORECASE):
            full_id = subitem.get("id")
            item_id = MonokakidoUtils.get_subitem_id(full_id)

            entry = idiom_keys.get(item_id)
            if not entry:
                raise ValueError(f"\nNo error for subitem: {full_id}")

            kanji_forms = entry['kanji']
            reading_forms = entry['readings']

            filtered_keys = ExpressionFilter.filter_full_forms(kanji_forms, reading_forms)
            if any(KanjiUtils.is_katakana(c) for c in HTMLUtils.extract_field(subitem, "headword")):
                print(f"Katakana found: {filtered_keys}, context: {HTMLUtils.extract_field(subitem, 'headword')}")

            for kanji, reading in filtered_keys:
                count += self.parse_entry(jaconv.kata2hira(kanji), jaconv.kata2hira(reading), subitem, ignore_expressions=False)

        return count


    def _parse_non_split_idiom_entry(self, soup: bs4.BeautifulSoup, idiom_keys: dict) -> int:
        count = 0

        entry = idiom_keys.get(list(idiom_keys.keys())[0])
        kanji_forms = [jaconv.kata2hira(k) for k in entry['kanji']]
        reading_forms = [jaconv.kata2hira(r) for r in entry['readings']]

        filtered_keys = ExpressionFilter.filter_full_forms(kanji_forms, reading_forms)
        if not filtered_keys:
            print(f"\nNo idiom key matches: kanji_forms={kanji_forms}, reading_forms={reading_forms}")

        for kanji, reading in filtered_keys:
            count += self.parse_entry(kanji, reading, soup, ignore_expressions=False)

        return count