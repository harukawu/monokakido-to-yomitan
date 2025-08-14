import os
from typing import Optional
import bs4

from config import DictionaryConfig
from .xml_parser import XMLParser
from core.yomitan import DicEntry


class YomitanParser(XMLParser):
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

        from core.yomitan import YomitanDictionary
        self.dictionary = YomitanDictionary(config.dict_name, config.term_bank_folder)
        self.normalization_strategy = config.create_normalization_strategy()


    def parse_entry(self,
                    term: str,
                    reading: str,
                    soup: bs4.BeautifulSoup | bs4.PageElement | bs4.Tag | bs4.NavigableString,
                    info_tag: Optional[str] = '',
                    pos_tag: Optional[str] = '',
                    search_rank: Optional[int] = 0,
                    seq_num: Optional[int] = 0,
                    ignore_expressions: Optional[bool] = False) -> int:
        if not reading or reading is None:
            reading = ''

        if not term:
            term = reading
            reading = ''

        entry = DicEntry(
            term,
            reading,
            info_tag=info_tag,
            pos_tag=pos_tag,
            search_rank=search_rank,
            seq_num=seq_num
        )

        for tag in soup.find_all(recursive=False):
            yomitan_element = self.convert_element_to_yomitan(tag, ignore_expressions=ignore_expressions)

            if yomitan_element:
                entry.add_element(yomitan_element)
            else:
                print(f"Failed parsing entry: {term}, reading: {reading}")
                return 0

        self.dictionary.add_entry(entry)
        return 1


    def export(self, output_path: Optional[str] = None) -> None:
        os.makedirs(self.config.term_bank_folder, exist_ok=True)
        self.dictionary.export()