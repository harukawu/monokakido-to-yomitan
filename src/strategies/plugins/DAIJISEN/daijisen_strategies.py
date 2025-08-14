import bs4

from strategies.link import DefaultLinkHandlingStrategy
from strategies.image import DefaultImageHandlingStrategy


class DaijisenLinkHandlingStrategy(DefaultLinkHandlingStrategy):

    def get_href(self, html_glossary: bs4.element.Tag) -> str:
        href = html_glossary.get("href", "")

        if href.startswith('map:ll='):
            # Extract coordinates from the href and create an Apple maps link
            try:
                coords_part = href.split("map:ll=")[1].split("&")[0]
                lat, lng = coords_part.split(",")

                href = f"https://maps.apple.com/?ll={lat},{lng}"
                return href
            except Exception as e:
                print(f"\nError processing map coordinates: {e}")

        elif "blue" in html_glossary.get("class", bs4.element.AttributeValueList()):
            collected_text = []
            for child in html_glossary.contents:
                if child.name == "wari":
                    continue
                if isinstance(child, str):  # Plain text
                    collected_text.append(child.strip())
                elif child.name:  # Other elements, preserve their text
                    collected_text.append(child.get_text(strip=True))

            href = str("".join(filter(None, collected_text)))
            return href

        return ""


class DaijisenImageHandlingStrategy(DefaultImageHandlingStrategy):

    def get_src_path(self, html_glossary: bs4.element.Tag) -> str:
        src_path = html_glossary.get("src", "")
        if src_path.lower().endswith('.heic'):
            src_path = src_path[:-5] + '.avif'

        if "Audio.png" in src_path:
            return ""

        return src_path