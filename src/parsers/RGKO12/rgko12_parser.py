import os
import bs4
import re
from typing import List, Tuple

from parsers.Monokakido.parser import MonokakidoParser
from config import DictionaryConfig


class RGKO12Parser(MonokakidoParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    @staticmethod
    def is_tsukaiwake_entry(soup: bs4.BeautifulSoup) -> Tuple[bool, str]:
        header_element = soup.find("table", class_="使い分け ヘッダあり")
        main_element = soup.find("table", class_="使い分け")

        index = soup.find("entry-index")
        if index:
            index = index.get_text(strip=True)

        if main_element or header_element:
            return True, index

        return False, ""

    @staticmethod
    def get_tsukaiwake_entries(index_str: str) -> List[Tuple[str, str]]:
        EXCLUDE_PATTERNS = [
            r'\{RB:活:かつ\}',
            r'\{RB:用:よう\}',
            r'\{RB:関:かん\}',
            r'\{RB:連:れん\}',
            r'\{RB:敬:けい\}',
            r'\{RB:語:ご\}',
            r'\{RB:参:さん\}',
            r'\{RB:考:こう\}'
        ]

        cleaned_str = index_str
        for pattern in EXCLUDE_PATTERNS:
            cleaned_str = re.sub(pattern, '', cleaned_str)

        variants = cleaned_str.split('・')
        pairs = []

        for variant in variants:
            if not variant.strip():
                continue

            # Extract all remaining RB tags
            rb_tags = re.findall(r'\{RB:([^:]+):([^}]+)\}', variant)

            if not rb_tags:
                # Handle cases like "ほどく" without RB tags
                kanji = variant
                reading = variant
                pairs.append((kanji, reading))
                continue

            # Extract remaining text after RB tags
            remaining_text = re.sub(r'\{RB:[^}]+\}', '', variant)

            # Build kanji and reading from RB tags and remaining text
            kanji_parts = []
            reading_parts = []

            for kanji, reading in rb_tags:
                kanji_parts.append(kanji)
                reading_parts.append(reading)

            kanji = ''.join(kanji_parts) + remaining_text
            reading = ''.join(reading_parts) + remaining_text

            pairs.append((kanji, reading))

        return pairs

    def _parse_entries_from_html(self, soup: bs4.BeautifulSoup) -> int:
        count = 0

        _, index = RGKO12Parser.is_tsukaiwake_entry(soup)
        tsukaiwake_entries = RGKO12Parser.get_tsukaiwake_entries(index)
        for kanji, kana in tsukaiwake_entries:
            info_tag, pos_tag = self.pos_tag_strategy.get_from_term(kanji)
            count += self.parse_entry(kanji, kana, soup, pos_tag=pos_tag, ignore_expressions=True)

        return count

    def _process_file(self, filename: str, file_content: str) -> int:
        entry_count = 0
        filename_without_ext = os.path.splitext(filename)[0]

        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))

        # Parse xml
        soup = bs4.BeautifulSoup(file_content, "xml")

        is_tsukaiwake_entry, _ = RGKO12Parser.is_tsukaiwake_entry(soup)
        if is_tsukaiwake_entry:
            entry_count += self._parse_entries_from_html(soup)

        elif entry_keys:
            entry_count += self._parse_head_entries(soup, entry_keys, filename)

        return entry_count
