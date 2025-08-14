import os
import bs4

from utils.lang import KanjiUtils
from utils.lang import ExpressionFilter

from core.parser_module import YomitanParser
from parsers.NDS.nds_utils import NDSUtils
from parsers.KJT.kjt_utils import KJTUtils
from config import DictionaryConfig
from handlers import process_unmatched_entries
from index import JukugoIndexReader


class NDSParser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        self.subitem_index_reader = JukugoIndexReader(os.path.join(os.path.dirname(config.index_path), "idiom_prefix.tsv"))


    def _process_file(self, filename: str, xml: str):
        count = 0
        filename_without_ext = os.path.splitext(filename)[0]

        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))

        if not entry_keys:
            print(f"No entry keys for entry: {filename_without_ext}")

        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")

        if soup.find("子項目"):
            count += self._handle_subitems(soup, filename_without_ext)

        # Use reading for normalisation (Whether to convert keys to hiragana or keep katakana)
        headword = NDSUtils.extract_field(soup, "見出")
        if not headword:
            print(f"No headword for entry: {filename_without_ext}\nKeys: {entry_keys}")

        # Normalise and match keys
        normalized_keys = self.normalization_strategy.normalize_keys(entry_keys, headword)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, normalized_keys, matched_key_pairs, self.manual_handler
        )

        # Determine search ranking (rank kana entries higher)
        has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
        search_rank = 1 if not has_kanji else 0

        # Process each key pair
        for kanji_part, kana_part in matched_key_pairs:
            if kanji_part:
                pos_tag, info_tag = self.pos_tag_strategy.get_from_html(soup, kanji_part, kana_part)
                count += self.parse_entry(
                    kanji_part, kana_part, soup, pos_tag=pos_tag, search_rank=search_rank, ignore_expressions=True
                )
            elif kana_part:
                count += self.parse_entry(
                    kana_part, "", soup, search_rank=search_rank, ignore_expressions=True
                )

        return count


    def _handle_subitems(self, soup: bs4.BeautifulSoup, filename_without_ext: str) -> int:
        count = 0

        subitem_entries = self.subitem_index_reader.get_organized_entries_for_page(filename_without_ext)
        for subitem in soup.findAll("子項目"):
            full_id = subitem.get("id")
            item_id = KJTUtils.get_item_id(full_id)

            subitem_entry = subitem_entries.get(item_id)
            if not subitem_entry:
                print(f"No entry for subitem: {full_id} in file: {filename_without_ext}")
                continue

            kanji_forms = subitem_entry['kanji']
            reading_forms = subitem_entry['readings']

            filtered_keys = ExpressionFilter.filter_full_forms(kanji_forms, reading_forms)
            context = NDSUtils.extract_field(subitem, "子見出")

            for kanji, reading in filtered_keys:
                normalized_kanji = self.normalization_strategy.normalize_keys([kanji], context)
                normalized_reading = self.normalization_strategy.normalize_keys([reading], context)
                count += self.parse_entry(normalized_kanji[0], normalized_reading[0], subitem, ignore_expressions=False)


            if len(filtered_keys) == 0:
                print(f"\nNo filtered keys for subitem {item_id}\nFile: {filename_without_ext}\nContext: {context}")

        return count