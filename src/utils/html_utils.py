import re
import bs4
import jaconv
from typing import Tuple, List

from utils.lang import KanjiUtils


class HTMLUtils:

    @staticmethod
    def extract_field(soup: bs4.BeautifulSoup | bs4.PageElement | bs4.Tag | bs4.NavigableString, field: str) -> str:
        headword = ""

        head_element = soup.find(field)
        if head_element:
            headword = head_element.text.strip()

        return headword

    @staticmethod
    def extract_ruby_text(element: bs4.element.Tag) -> str:
        for ruby_tag in element.find_all("ruby"):
            ruby_tag.unwrap()

        for rt_tag in element.find_all("rt"):
            rt_tag.decompose()

        cleaned_word = "".join(element.text).strip()
        cleaned_word = KanjiUtils.clean_headword(cleaned_word)

        return cleaned_word

    @staticmethod
    def extract_ruby_text_and_reading(element: bs4.element.Tag) -> Tuple[str, str]:
        readings = []
        base_expression = []

        for tag in element.contents:
            if tag.name == "ruby":
                rb = tag.find("rb")
                rt = tag.find("rt")

                if rb:
                    base_expression.append(rb.text.strip())
                if rt:
                    readings.append(rt.text.strip())
            elif isinstance(tag, str):
                text = tag.strip()
                if text:
                    base_expression.append(text)
                    readings.append(text)

        text_without_furigana = "".join(base_expression).strip()
        text_reading = "".join(readings).strip()

        text_without_furigana = KanjiUtils.clean_headword(text_without_furigana)
        text_without_furigana = re.sub("・", "", text_without_furigana)

        text_reading = KanjiUtils.clean_reading(text_reading)

        return text_without_furigana, text_reading


    @staticmethod
    def wrap_example_elements(soup: bs4.BeautifulSoup, body_field: str="body", body_class: str=None, example_field: str="example") -> bs4.BeautifulSoup:
        body = soup.find(body_field, class_=body_class)
        if not body:
            return soup

        all_examples = body.find_all(example_field)
        if not all_examples:
            return soup

        groups = []
        current_group = []

        for example in all_examples:
            if not current_group:
                # Start new group
                current_group = [example]
            else:
                # Check if this example is consecutive to the last one in current group
                last_example = current_group[-1]
                if HTMLUtils.are_consecutive_siblings(last_example, example):
                    current_group.append(example)
                else:
                    # End current group and start new one
                    if len(current_group) > 0:
                        groups.append(current_group)
                    current_group = [example]

        # Don't forget the last group
        if len(current_group) > 0:
            groups.append(current_group)

        # Wrap each group in details/summary
        for group in groups:
            HTMLUtils.wrap_examples_in_details(soup, group)

        return soup

    @staticmethod
    def are_consecutive_siblings(elem1: bs4.Tag | bs4.PageElement, elem2: bs4.Tag | bs4.PageElement) -> bool:
        """Check if two elements are consecutive siblings (ignoring whitespace)."""
        current = elem1
        while current:
            current = current.next_sibling
            # Skip text nodes that are just whitespace
            if hasattr(current, 'text') and current.get_text(strip=True) == '':
                continue

            if current == elem2:
                return True
            # If we found any other element, they are not consecutive
            if hasattr(current, 'name'):
                return False

        return False

    @staticmethod
    def wrap_examples_in_details(soup: bs4.BeautifulSoup, examples: List[bs4.Tag | bs4.PageElement]) -> None:
        if len(examples) < 1:
            return

        first_example = examples[0]

        details = soup.new_tag('details')
        summary = soup.new_tag('summary')
        summary.append(f"例文{jaconv.h2z(str(len(examples)), digit=True)}件")
        details.append(summary)

        first_example.insert_before(details)

        # Move all examples into the details element
        for example in examples:
            details.append(example.extract())