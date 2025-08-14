from strategies.image import GaijiImageHandlingStrategy


class ShinjigenImageHandlingStrategy(GaijiImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "1E0D.png": {
                "text": "ḍ",
                "class": "diacritic"
            },
            "1E43.png": {
                "text": "ṃ",
                "class": "diacritic"
            },
            "1E45.png": {
                "text": "ṅ",
                "class": "diacritic"
            },
            "1E47.png": {
                "text": "ṇ",
                "class": "diacritic"
            },
            "1E63.png": {
                "text": "ṣ",
                "class": "diacritic"
            },
            "1ECD.png": {
                "text": "ọ",
                "class": "diacritic"
            },
            "ontenka.png": {
                "text": "→",
                "class": "音転化"
            },
            "一。.png": {
                "text": "一。",
                "class": "kaeritenimg"
            },
            "一、.png": {
                "text": "一、",
                "class": "kaeritenimg"
            },
            "一レ.png": {
                "text": "一レ",
                "class": "kaeritenre"
            },
            "二I.png": {
                "text": "二|",
                "class": "kaeritennum"
            },
            "四I.png": {
                "text": "四|",
                "class": "kaeritennum"
            },
            "中I.png": {
                "text": "中|",
                "class": "kaeritennum"
            },
            "上レ.png": {
                "text": "上レ",
                "class": "kaeritenjoure"
            },
            "上、.png": {
                "text": "上、",
                "class": "kaeritenimg"
            },
            "三レ.png": {
                "text": "三レ",
                "class": "kaeritensanre"
            },
            "三I.png": {
                "text": "三|",
                "class": "kaeritennum"
            },
            "甲レ.png": {
                "text": "甲レ",
                "class": "kaeritensanre"
            },
            "下I.png": {
                "text": "下|",
                "class": "kaeritennum"
            }
        }
