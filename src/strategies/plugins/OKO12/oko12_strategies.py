import bs4

from strategies.image import GaijiImageHandlingStrategy
from strategies.link import DefaultLinkHandlingStrategy


class OKO12LinkHandlingStrategy(DefaultLinkHandlingStrategy):
    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        collected_text = []
        for child in html_glossary.contents:
            if child.name == "mlg":
                continue
            if isinstance(child, str):  # Plain text
                collected_text.append(child.strip())
            elif child.name:  # Other elements, preserve their text
                collected_text.append(child.get_text(strip=True))

        if not collected_text:
            return ""

        return "".join(filter(None, collected_text)).strip()


class OKO12ImageHandlingStrategy(GaijiImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "arrow_both_h_thin.svg": {
                "text": "↔",
                "class": "矢印"
            },
            "arrow_both_v_thin.svg": {
                "text": "↔",
                "class": "矢印"
            },
            "arrow_down.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "arrow_right.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "dollar2.svg": {
                "text": "$",
                "class": "外字"
            },
            "maruko.svg": {
                "text": "高",
                "class": "maru"
            },
            "maruchu.svg": {
                "text": "中",
                "class": "maru"
            }
        }
