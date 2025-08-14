from typing import Optional
import bs4


class MonokakidoUtils:

    @staticmethod
    def get_subitem_id(full_id: str) -> Optional[str]:
        parts = full_id.split('-')
        if len(parts) != 2:
            print(f"Invalid ID format: {full_id}")
            return None

        # Get the last part which contains the item number
        item_part = parts[1]

        # Always take the last 3 characters (works for both hex and decimal)
        last_three = item_part[-3:]

        try:
            # Convert just the last 3 hex digits to decimal
            decimal_value = int(last_three, 16)

            # Convert to 3-digit string
            item_id = f"{decimal_value:03d}"
        except ValueError:
            print(f"Failed to convert hex ID: {last_three}")
            return None

        return item_id
