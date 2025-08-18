import bs4
#import jaconv

from core.yomitan import DicEntry
from parsers.Monokakido.parser import MonokakidoParser
from utils import HTMLUtils


class MeikyoParser(MonokakidoParser):
    """
    def _preprocess_content(self, soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        meanings = soup.find_all('meaning')
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
    """

    def _parse_entries_from_html(self, soup: bs4.BeautifulSoup) -> int:
        count = 0

        for child in soup.find_all("child-item"):
            head_element = child.find("headword", class_="子見出し")
            if not head_element:
                print(f"Found no headword element for expression in: {child}")
                continue

            expression, reading = HTMLUtils.extract_ruby_text_and_reading(head_element)
            if not expression:
                print(f"No expression in: {child}")
                continue
            elif not reading:
                print(f"No reading for expression: {expression} in:\n{child}")

            _, pos_tag = self.pos_tag_strategy.get_from_term(expression)
            entry = DicEntry(expression, reading, pos_tag=pos_tag)
            yomitan_element = self.convert_element_to_yomitan(child, ignore_expressions=False)

            if yomitan_element:
                entry.add_element(yomitan_element)
                self.dictionary.add_entry(entry)
                count += 1

        return count
