import regex as re
import bs4
import jaconv
from typing import Dict, Tuple, Optional

from .pos_tag_strategies import DefaultPosTagStrategy
from utils.lang import KanjiUtils


class NDSPosTagStrategy(DefaultPosTagStrategy):
    NIDAN_CATEGORY_REGEX = re.compile(r'(\p{Katakana})[下上]二')

    def __init__(self, jmdict_path: Optional[str] = None):
        super().__init__(jmdict_path)

        self.base_pos_map: Dict[str, str] = {
            "名": "n",
            "代名": "pn",
            "固有名詞": "n-pr",
            "形動": "adj-na",
            "形シク": "adj-shiku",
            "形ク": "adj-ku",
            "形口": "adj-i",
            "形動タリ": "adj-t",
            "形動ナリ・タリ": "adj-nari adj-t",
            "連体": "adj-pn",
            "副": "adv",
            "接続": "conj",
            "感動": "int",
            "格助": "prt",
            "副助": "prt",
            "係助": "prt",
            "接助": "prt",
            "終助": "prt",
            "助動": "aux",
            "接尾": "suf",
            "連語": "exp",
            "枕": "exp"
        }

        self.pos_tag_map: Dict[str, str] = {
            "自": "vi",
            "他": "vt",
            "下一": "v1",
            "カ変": "vk",
            "サ変": "vs",
            "ナ変": "vn",
            "ラ変": "vr",
        }

        self.kana_map = {
            "カ": "k", "ハ": "h", "サ": "s", "ヤ": "y",
            "ダ": "d", "ラ": "r", "マ": "m", "ナ": "n",
            "ガ": "g", "バ": "b", "タ": "t", "ワ": "u"
        }

        self.yodan_category_regex = r'\p{Katakana}(?=.*四)'
        self.godan_category_regex = r'\p{Katakana}(?=.*五)'

    def get_from_html(self, soup: bs4.BeautifulSoup, term: str, reading: str) -> Tuple[str, str]:
        pos_info = self._extract_pos_info(soup, reading)

        # try to extract from jmdict
        if not pos_info:
            _, pos_info = self.get_from_term(term)

        # TODO: maybe add info tag idk
        # href $gengo

        return pos_info, ""

    def _extract_pos_info(self, soup: bs4.BeautifulSoup, reading: str) -> Optional[str]:
        pos_section = soup.find("語義")
        if not pos_section:
            return None

        pos_tags = set()
        for element in pos_section.find_all("a"):
            element_text = element.get_text(strip=True)
            if not any(c in element_text for c in ['〘', '〙']):
                continue

            element_text = KanjiUtils.clean_headword(element_text)

            mapped_tag = self.base_pos_map.get(element_text)
            if mapped_tag:
                pos_tags.add(mapped_tag)
            else:
                verb_tags = self._parse_verb_pattern(element_text, reading)
                pos_tags.update(verb_tags)

            for key, val in self.pos_tag_map.items():
                if key in element_text:
                    pos_tags.add(val)

        return ' '.join(pos_tags)


    def _parse_verb_pattern(self, element_text: str, reading: str) -> set[str]:
        tags = set()

        if element_text.startswith('自'):
            tags.add('vi')
        elif element_text.startswith('他'):
            tags.add('vt')

        if '下一' in element_text:
            tags.add('v1')
        elif '上一' in element_text:
            tags.add('v1')
        elif '下二' in element_text:
            tags.add(self._get_nidan_category(element_text, 's'))
        elif '上二' in element_text:
            tags.add(self._get_nidan_category(element_text, 'k'))

        if '四' in element_text:
            tags.add(self._get_yodan_category(element_text))
        if '五' in element_text:
            tags.add(self._get_godan_category(element_text, reading))

        if 'カ変' in element_text:
            tags.add('vk')
        elif 'サ変' in element_text:
            tags.add('vs')
        elif 'ラ変' in element_text:
            tags.add('vr')
        elif 'ナ変' in element_text:
            tags.add('vn')

        return tags


    def _get_nidan_category(self, element_text: str, class_type: str) -> Optional[str]:
        katakana_char = ''.join([c for c in element_text if KanjiUtils.is_katakana(c)])
        if not katakana_char:
            return f"v2-{class_type}"

        if katakana_char in self.kana_map:
            return f"v2{self.kana_map[katakana_char]}-{class_type}"

        return f"v2-{class_type}"


    def _get_yodan_category(self, element_text: str) -> str:
        match = re.search(self.yodan_category_regex, element_text)
        if match:
            katakana_char = match.group()
            if katakana_char in self.kana_map:
                return f"v4{self.kana_map[katakana_char]}"

        return "v4"


    def _get_godan_category(self, element_text: str, reading: str) -> str:
        match jaconv.kata2hira(reading):
            case s if s.endswith("ある") or s.endswith("有る"):
                return "v5aru"
            case s if any(s.endswith(c) for c in ["いく", "ゆく", "行く", "逝く"]):
                return "v5k-s"
            case s if s.endswith("うる"):
                return "v5uru"

        match = re.search(self.godan_category_regex, element_text)
        if match:
            katakana_char = match.group()
            if katakana_char in self.kana_map:
                return f"v5{self.kana_map[katakana_char]}"

        return "v5"
