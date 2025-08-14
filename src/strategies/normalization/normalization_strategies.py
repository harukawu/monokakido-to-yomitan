from abc import ABC, abstractmethod
from typing import List, Optional
import bs4
import jaconv

from utils.lang import KanjiUtils


class NormalizationStrategy(ABC):
    @abstractmethod
    def normalize_keys(self, entry_keys: List[str], soup: bs4.BeautifulSoup) -> List[str]:
        pass

    @abstractmethod
    def get_context(self, soup: bs4.BeautifulSoup) -> str:
        pass


class DefaultNormalizationStrategy(NormalizationStrategy):
    def __init__(self, tag_name: Optional[str] = "", class_name: Optional[str] = None):
        self.tag_name = tag_name
        self.class_name = class_name

    def get_context(self, soup: bs4.BeautifulSoup) -> str:
        context = ""

        element = soup.find(self.tag_name, class_=self.class_name) if self.class_name else soup.find(self.tag_name)
        if element:
            context = element.text.strip()

        return context


    def normalize_keys(self, entry_keys: List[str], soup: bs4.BeautifulSoup) -> List[str]:
        context = self.get_context(soup)

        if all(KanjiUtils.is_kanji(c) for c in context):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        elif any(KanjiUtils.is_katakana(c) for c in context):
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]

        return normalized_keys