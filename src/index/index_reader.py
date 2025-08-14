import os
from typing import List, Dict, Any
from collections import defaultdict
from tqdm import tqdm


class IndexReader:
    def __init__(self, index_file_path: str) -> None:
        """Initialize with the path to the index_d.tsv file"""
        self.index_file_path = index_file_path
        self.dict_data = {}  # Dictionary mapping keys to filenames
        self.file_to_keys = defaultdict(list)  # Reverse mapping: filename -> keys
        self.load_index()

    def load_index(self) -> None:
        """Load the index file and build both mappings"""
        if not os.path.exists(self.index_file_path):
            raise FileNotFoundError(f"Index file not found: {self.index_file_path}")

        # Count total lines for progress tracking
        with open(self.index_file_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)

        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"

        with open(self.index_file_path, 'r', encoding='utf-8') as f, \
                tqdm(total=total_lines, desc="索引読込中", unit="行", bar_format=bar_format, ascii="░▒█") as pbar:

            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    print(f"Found a malformed line: {parts}")
                    continue

                key = parts[0]
                filenames = parts[1:]

                self.dict_data[key] = filenames

                # Build reverse mapping
                for filename in filenames:
                    self.file_to_keys[filename].append(key)

                pbar.update(1)

    def get_keys_for_file(self, filename: str) -> List[str]:
        """Get all dictionary keys associated with a given filename"""
        return self.file_to_keys.get(filename, [])

    def process_all_files(self) -> None:
        """Process all files and show their associated keys"""
        count = 0
        import random
        shuffled_items = list(self.file_to_keys.items())
        random.shuffle(shuffled_items)

        for filename, keys in tqdm(shuffled_items, desc="進歩", unit="事項"):
            if count > 20:
                break

            print(f"Filename: {filename}")
            print(f"Associated keys: {', '.join(keys)}")
            print("-" * 50)
            count += 1

    def add_entry(self, filename: str, key: str) -> bool:
        """
        Add a key-filename entry to the index.
        :param filename: The filename to associate with the key
        :param key: The key to add

        :returns bool: True if entry was added, False if key-filename pair already exists
        """
        # Check if this key-filename pair already exists
        if key in self.dict_data and filename in self.dict_data[key]:
            return False  # Already exists

        if key in self.dict_data:
            # Key exists, add filename if not already present
            if filename not in self.dict_data[key]:
                self.dict_data[key].append(filename)
        else:
            # New key
            self.dict_data[key] = [filename]

        # Add to reverse mapping
        if key not in self.file_to_keys[filename]:
            self.file_to_keys[filename].append(key)

        return True

    def _write_to_index_file(self) -> None:
        """
        Write the updated entry to the index file.
        This rewrites the entire file to maintain consistency.
        """
        with open(self.index_file_path, 'w', encoding='utf-8') as f:
            for k, filenames in self.dict_data.items():
                line = k + '\t' + '\t'.join(filenames) + '\n'
                f.write(line)


class JukugoIndexReader:

    def __init__(self, index_file_path: str):
        self.index_file_path = index_file_path
        self.page_to_items = defaultdict(list)
        self.grouped_entries = defaultdict(lambda: defaultdict(set))  # page_id -> item_id -> set of keys

        self.load_index()

    def load_index(self):
        """Load the index file and build mappings"""
        if not os.path.exists(self.index_file_path):
            raise FileNotFoundError(f"Index file not found: {self.index_file_path}")

        # Count total lines for progress tracking
        with open(self.index_file_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)

        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"

        with open(self.index_file_path, 'r', encoding='utf-8') as f, \
                tqdm(total=total_lines, desc="索引読込中", unit="行", bar_format=bar_format, ascii="░▒█") as pbar:

            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    print(f"Found a malformed line: {parts}")
                    continue

                key = parts[0]  # The jukugo word
                reference_ids = parts[1:]

                # Process each reference ID to build the page_to_items mapping
                for ref_id in reference_ids:
                    try:
                        ref_parts = ref_id.split('-')
                        if len(ref_parts) < 2:
                            continue

                        page_id = ref_parts[0]
                        item_id = ref_parts[1]

                        self.page_to_items[page_id].append({"key": key, "item_id": [item_id]})
                        self.grouped_entries[page_id][item_id].add(key)

                    except ValueError:
                        print(f"Invalid reference ID format: {ref_id}")

                pbar.update(1)

    def get_grouped_entries_for_page(self, page_id: str) -> Dict[str, List[str]]:
        if page_id not in self.grouped_entries:
            return {}

        result = {}
        for item_id, keys in self.grouped_entries[page_id].items():
            result[item_id] = sorted(list(keys))

        return result

    def categorize_entries(self, entries: List[str]) -> Dict[str, List[str]]:
        from utils import KanjiUtils

        kanji_entries = []
        kana_entries = []

        for entry in entries:
            if any(KanjiUtils.is_kanji(c) for c in entry):
                kanji_entries.append(entry)
            else:
                kana_entries.append(entry)

        return {
            'kanji': kanji_entries,
            'readings': kana_entries
        }

    def get_organized_entries_for_page(self, page_id: str) -> dict[str, Any]:
        """
        Get entries organized by item_id with categorized keys.
        Returns a list of dictionaries, each containing:
        - item_id: The item identifier
        - kanji: List of kanji forms
        - readings: List of reading forms (kana)
        """
        from utils import KanjiUtils  # Import here to avoid circular imports
        import jaconv

        grouped = self.get_grouped_entries_for_page(page_id)
        result = {}

        for item_id, keys in grouped.items():
            categorized = self.categorize_entries(keys)

            result[item_id] = {
                'kanji': categorized['kanji'],
                'readings': categorized['readings']
            }

        return result
