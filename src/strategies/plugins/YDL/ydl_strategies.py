from strategies.image import GaijiImageHandlingStrategy


class YDLImageHandlingStrategy(GaijiImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "arrow-thin-h.svg": {
                "text": "⇀",
                "class": "矢印"
            },
            "arrow-thin.svg": {
                "text": "⇀",
                "class": "矢印"
            },
            "arrow-h.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "arrow.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "135.svg": {
                "text": "-",
                "class": "ハイフン"
            }
        }
