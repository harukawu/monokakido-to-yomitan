import json
import bs4
from typing import List

from utils import FileUtils

from core.parser_module import YomitanParser
from config import DictionaryConfig

class ShinjigenParser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        self.dict_data = FileUtils.load_mdx_json(config.dict_path)


    @staticmethod
    def extract_entry_keys(entry: str) -> List[str]:
        if not entry:
            return []

        entry = entry.replace('《', '').replace('》', '')
        entries = entry.split('|')
        return entries
        
        
    def _process_file(self, filename: str, file_content: str) -> int:
        count = 0

        file_content_dict = json.loads(file_content)
        for key, val in file_content_dict.items():
            entry_keys = ShinjigenParser.extract_entry_keys(key)
            soup = bs4.BeautifulSoup(val, "lxml")

            for entry in entry_keys:
                count += self.parse_entry(entry, "", soup)

        return count