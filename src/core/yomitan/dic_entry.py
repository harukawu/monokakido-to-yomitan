

class DicEntry:
    def __init__(self, word, reading, info_tag="", pos_tag="", search_rank=0, seq_num=0, definition=None):
        self.word = word
        self.reading = reading
        self.info_tag = info_tag
        self.pos_tag = pos_tag
        self.search_rank = search_rank
        self.seq_num = seq_num
        self.content = []
        self.structured_content = False
        if definition:
            self.set_simple_content(definition)

        self._allowed_elements = ["br", "ruby", "rt", "rp", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "span",
                            "div",
                            "ol", "ul", "li", "img", "a", "details", "summary"]
        self._allowed_href_elements = ["a"]


    def to_list(self):
        if self.structured_content:
            content = [{"type": "structured-content", "content": self.content}]
        else:
            content = self.content
        return [
            self.word,
            self.reading,
            self.info_tag,
            self.pos_tag,
            self.search_rank,
            content,
            self.seq_num,
            ""
        ]


    def print_content(self):
        print(self.content)


    def add_element(self, element):
        self.validate_element(element)
        self.content.append(element)
        self.structured_content = True


    def set_simple_content(self, definition):
        if isinstance(definition, str):
            self.content = [definition]
        elif isinstance(definition, list):
            self.content = definition
        else:
            raise ValueError("Definition must be a string or a list of strings")
        self.structured_content = False


    def set_link_content(self, definition, link):
        self.content = [
            create_html_element("ul", [
                create_html_element("li", definition)
            ]),
            create_html_element("ul", [
                create_html_element("li", [create_html_element("a", link, href=link)])
            ], style={"listStyleType": "\"⧉\""})
        ]
        self.structured_content = True


    def validate_element(self, element):
        if element["tag"] not in self._allowed_elements:
            raise ValueError(f"Unsupported HTML element: {element['tag']}")

        if "href" in element and element["tag"] not in self._allowed_href_elements:
            raise ValueError(f"The 'href' attribute is not allowed in the '{element['tag']}' element, only <a>.")

        if "content" in element:
            content = element["content"]

            # If content is None, that's a problem
            if content is None:
                raise ValueError(f"Element '{element['tag']}' has 'None' as content, which is invalid")

            # If content is a list, validate each child element
            elif isinstance(content, list):
                for i, child_element in enumerate(content):
                    try:
                        # Recursively validate child elements
                        if isinstance(child_element, dict):
                            self.validate_element(child_element)
                        elif not isinstance(child_element, str):
                            raise ValueError \
                                (f"Element {element['tag']} has invalid content at index {i}: expected string or element dict, got {type(child_element).__name__} - Value: {repr(child_element)}")
                    except ValueError as e:
                        # Enhance error message with path information
                        raise ValueError(f"In {element['tag']} > content[{i}]: {str(e)}")

            # If content is not a string or list, it's invalid
            elif not isinstance(content, str):
                raise ValueError \
                    (f"Element '{element['tag']}' has invalid content: expected string or list of elements, got {type(content).__name__} - Value: {repr(content)}")


def create_html_element(tag, content=None, id=None, title=None, href=None, style=None, data=None, rowSpan=None, colSpan=None):
    element = {"tag": tag}
    if tag != "br":
        if isinstance(content, str):
            element["content"] = content
        else:
            element["content"] = content
    if id:
        element["id"] = id
    if title:
        element["title"] = title
    if href:
        element["href"] = href
    if style:
        element["style"] = style
    if data:
        element["data"] = data
    if rowSpan:
        element["rowSpan"] = int(rowSpan)
    if colSpan:
        element["colSpan"] = int(colSpan)

    return element