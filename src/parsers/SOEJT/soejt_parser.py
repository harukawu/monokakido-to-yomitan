import os
import bs4
import jaconv

from config import DictionaryConfig
from core.parser_module import YomitanParser

class SOEJTParser(YomitanParser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)

    # ----- Preprocessing ----- #

    @staticmethod
    def wrap_example_elements(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        body = soup.find(class_='childbody')
        if not body:
            return soup

        all_examples = body.find_all('example')
        groups = []
        current_group = []

        for example in all_examples:
            if not current_group:
                # Start new group
                current_group = [example]
            else:
                # Check if this example is consecutive to the last one in current group
                last_example = current_group[-1]
                if SOEJTParser.are_consecutive_siblings(last_example, example):
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
            SOEJTParser.wrap_examples_in_details(soup, group)

        return soup

    @staticmethod
    def are_consecutive_siblings(elem1, elem2):
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
    def wrap_examples_in_details(soup, examples):
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

    @staticmethod
    def replace_scale_header_arrows(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        scale_section = soup.find(class_='類語スケール')
        if not scale_section:
            return soup

        arrow_td = scale_section.find('td', class_='scale-header-arrow')
        if arrow_td:
            # Clear the content and add CSS arrow div
            arrow_td.clear()
            css_arrow = soup.new_tag('div', **{'class': 'css-arrow'})
            arrow_td.append(css_arrow)

            scale_head = scale_section.find('td', class_='scale-header')
            if scale_head:
                scale_head.decompose()

        return soup

    # Wrap elements in "details / summary" that should be collapsed
    def _preprocess_content(self, soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        return self.wrap_example_elements(soup)

    # ----- Parsing ----- #

    def _add_misc_xml_content(self, soup: bs4.BeautifulSoup, href: str, title: str) -> bs4.BeautifulSoup:
        if not href:
            return soup

        body = soup.find('body')
        href = href.zfill(10)

        try:
            xml_content = self.file_iterator.read_file(href + ".xml")
        except FileNotFoundError:
            return soup

        child_soup = bs4.BeautifulSoup(xml_content, "xml")
        if child_soup.find(class_='topchildbody'):
            return soup

        child_soup = self.replace_scale_header_arrows(child_soup)
        child_body = child_soup.find(class_='childbody')
        if child_body:
            new_element = soup.new_tag('details')
            summary = soup.new_tag('summary')
            summary.append(title)
            new_element.append(summary)
            new_element.append(child_body)

            body.append(new_element)

        return soup


    def _parse_top_entry(self, soup: bs4.BeautifulSoup) -> int:
        # extract synonym keys from 'entry-index' element (be sure to filter out the misc items)
        # for each synonym key, add an entry to the dictionary (they will have identical contents)
        count = 0
        entry_index = soup.find("entry-index")

        for key in entry_index.find_all("a"):
            key_text = key.get_text(strip=True)
            if key_text in ["類語グループ", "類語スケール", "文型 &amp; コロケーション", "文型 & コロケーション"]:
                soup = self._add_misc_xml_content(soup, key.get('href', ''), key_text)
                key.decompose()

        # Search rank 0 to ensure that this entry shows up before any definition entry
        for key in entry_index.find_all("a"):
            key_text = key.get_text(strip=True)
            count += self.parse_entry(key_text, "", soup, "", "", 0)

        return count

    def _process_file(self, filename: str, file_content: str) -> int:
        entry_count = 0
        entry_keys = list(set(self.index_reader.get_keys_for_file(os.path.splitext(filename)[0])))

        soup = bs4.BeautifulSoup(file_content, "xml")
        soup = self._preprocess_content(soup)

        if soup.find(class_='topchildbody'):
            entry_count += self._parse_top_entry(soup)

        # Child entries are just like normal dictionary entries, simply parse with the keys read from index
        # Search rank -1 to ensure that definition entries show up after the main thesaurus entry
        if soup.find(class_="childhead"):
            for key in entry_keys:
                entry_count += self.parse_entry(key, "", soup, "", "", -1)

        return entry_count
