import bs4

class NDSUtils:

    @staticmethod
    def extract_field(soup: bs4.BeautifulSoup, field: str) -> str:
        headword = ""

        head_element = soup.find(field)
        if head_element:
            headword = head_element.text.strip()

        return headword
