import bs4
from abc import ABC, abstractmethod
from typing import Tuple, Optional

from utils import FileUtils
from utils.lang import sudachi_rules

class PosTagStrategy(ABC):
    def __init__(self, jmdict_path: Optional[str] = None) -> None:
        self.jmdict_data = FileUtils.load_term_banks(jmdict_path) if jmdict_path else {}

    @abstractmethod
    def get_from_html(self, soup: bs4.BeautifulSoup, term: str, reading: str) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_from_term(self, term: str) -> Tuple[str, str]:
        pass


class DefaultPosTagStrategy(PosTagStrategy):
    def __init__(self, jmdict_path: Optional[str] = None) -> None:
        super().__init__(jmdict_path)

    def get_from_html(self, soup: bs4.BeautifulSoup, term: str, reading: str) -> Tuple[str, str]:
        pass

    def get_from_term(self, term: str) -> Tuple[str, str]:
        """Get part-of-speech tags for a term"""
        info_tag, pos_tag = self.jmdict_data.get(term, ["", ""])

        # Didn't find a POS tag match in JMdict, use sudachi instead
        if not pos_tag:
            sudachi_tag = sudachi_rules(term)
            return info_tag, sudachi_tag

        return info_tag, pos_tag