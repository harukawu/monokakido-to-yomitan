import os
import bs4

from .image_strategies import DefaultImageHandlingStrategy
from utils import FileUtils

class HashedImageStrategy(DefaultImageHandlingStrategy):

    def __init__(self, image_map_path: str) -> None:
        self.image_map = FileUtils.load_json(image_map_path)

    def get_src_path(self, html_glossary: bs4.element.Tag) -> str:
        src_path = html_glossary.get("src", "").lstrip("/")

        normalized_filename = self._get_normalized_filename(src_path)
        return normalized_filename

    def _get_normalized_filename(self, src_path: str) -> str:
        if not src_path:
            return ""

        original_filename = os.path.basename(src_path)

        # Try direct lookup first
        if original_filename in self.image_map:
            return src_path.replace(original_filename, self.image_map[original_filename])

        # Try normalized versions
        import unicodedata
        for norm_form in ["NFC", "NFD", "NFKC", "NFKD"]:
            normalized = unicodedata.normalize(norm_form, original_filename)
            if normalized in self.image_map:
                return src_path.replace(original_filename, self.image_map[normalized])

        return src_path