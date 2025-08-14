import bs4
import unicodedata
import jaconv

from core.yomitan import DicEntry
from config import DictionaryConfig
from core.parser_module import YomitanParser


class KNEJParser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    # ----- Preprocessing ----- #

    @staticmethod
    def _rename_valuable_subentries(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        """"
        Preprocesses the XML document. KNEJ has inconsistencies with subwords in entries.
        Some subentries only contain POS information such as "unutterableness n." in the entry "unutterable".
        It does not make sense to add these as single entries.

        :param soup: BeautifulSoup XML soup
        :return: BeautifulSoup processed XML soup
        """
        for subhead in soup.find_all("subhead"):
            meanings = subhead.find_all('meaning')

            # skip insignificant elements
            if meanings and len(meanings) == 1:
                children = list(meanings[0].children)

                # Meaning contains only a <pos> tag
                if len(children) == 1 and children[0].name == 'pos':
                    continue

            # this subhead makes sense to add as splitted entry
            subhead.name = "subitem"

        return soup

    @staticmethod
    def _wrap_example_elements(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        meanings = soup.find_all('meaning', class_=['level2', 'level3'])
        for meaning in meanings:
            new_element = soup.new_tag('details')

            examples = []
            next_sibling = meaning.next_sibling
            while next_sibling and hasattr(next_sibling, 'name') and next_sibling.name == 'example':
                following_sibling = next_sibling.next_sibling
                examples.append(next_sibling.extract())
                next_sibling = following_sibling

            if len(examples) == 0:
                continue

            summary = soup.new_tag('summary')
            summary.append(f"例文{jaconv.h2z(str(len(examples)), digit=True)}件")

            new_element.append(summary)
            for example in examples:
                new_element.append(example)

            meaning.insert_after(new_element)

        return soup

    # ----- Utils ----- #

    @staticmethod
    def extract_text_from_headword(soup: bs4.BeautifulSoup | bs4.PageElement | bs4.Tag | bs4.NavigableString,
                                   tag: str) -> str:
        headword_tag = soup.find(tag)
        if not headword_tag:
            return ""

        texts = []
        for child in headword_tag.children:
            if child.name in ('b', 'em'):
                text = child.get_text(strip=True)
                if text:  # Only add if there's actual text
                    # Normalise diacritics and remove combining characters
                    texts.append(text)

        return ' '.join(texts).replace("·", "").strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        decomposed = unicodedata.normalize('NFKD', text)
        filtered = ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')

        return filtered

    @staticmethod
    def _should_add_diactritics(soup: bs4.BeautifulSoup | bs4.PageElement) -> bool:
        pron_tag = soup.find("pron")
        if not pron_tag:
            return False

        italic_element_tag = pron_tag.find("i")
        if not italic_element_tag:
            return False

        return True

    # ----- Parsing ----- #

    def _parse_subentries(self, soup: bs4.BeautifulSoup) -> int:
        count = 0

        for subhead in soup.find_all(self.config.expression_element):
            headword = KNEJParser.extract_text_from_headword(subhead, "subheadword")
            normalized_headword = KNEJParser.normalize_text(headword)

            yomitan_element = self.convert_element_to_yomitan(subhead, ignore_expressions=False)

            if KNEJParser._should_add_diactritics(soup) and headword != normalized_headword:
                entry = DicEntry(headword, "")
                entry.add_element(yomitan_element)
                self.dictionary.add_entry(entry)

            normalized_entry = DicEntry(normalized_headword, "")
            normalized_entry.add_element(yomitan_element)
            self.dictionary.add_entry(normalized_entry)
            count += 1

        return count

    def _process_file(self, filename: str, file_content: str) -> int:
        entry_count = 0

        soup = bs4.BeautifulSoup(file_content, "xml")
        soup = KNEJParser._rename_valuable_subentries(soup)
        #soup = KNEJParser._wrap_example_elements(soup)

        headword = KNEJParser.extract_text_from_headword(soup, "headword")
        normalized_headword = KNEJParser.normalize_text(headword)

        entry_count += self.parse_entry(normalized_headword, "", soup, ignore_expressions=True)
        entry_count += self._parse_subentries(soup)

        variant = KNEJParser.extract_text_from_headword(soup, "variant")
        if variant and variant != headword:
            entry_count += self.parse_entry(variant, "", soup, ignore_expressions=True)

        if KNEJParser._should_add_diactritics(soup) and headword != normalized_headword and headword != variant:
            entry_count += self.parse_entry(headword, "", soup, ignore_expressions=True)

        return entry_count
