import os
import json
import regex as re


class YomitanDictionary:
    termbank_pattern = re.compile(r'(term_bank_(\d+)\.json$)')

    def __init__(self, dictionary_name: str, output_path: str):
        self.dictionary_name = dictionary_name
        self.output_path = output_path
        self._init_directory()
        # TODO: use a config instead with more info about the dictionary

        self.current_chunk = []
        self.total_entries = 0
        self.chunk_size = 10000


    def _init_directory(self):
        os.makedirs(self.output_path, exist_ok=True)

        for file in os.listdir(self.output_path):
            match = self.termbank_pattern.match(file)
            if match:
                os.remove(os.path.join(self.output_path, file))


    def add_entry(self, entry) -> bool:
        try:
            if not entry:
                raise ValueError("Entry must not be empty")

            self.current_chunk.append(entry)
            self.total_entries += 1

            if len(self.current_chunk) >= self.chunk_size:
                self._flush_chunk_to_disk()

            return True

        except ValueError:
            raise
        except Exception as e:
            print(f"Failed to add entry {entry}: {e}")
            return False


    def flush(self) -> bool:
        return self._flush_chunk_to_disk()


    def get_entry_count(self) -> int:
        return self.total_entries


    def _flush_chunk_to_disk(self) -> bool:
        if not self.current_chunk or len(self.current_chunk) == 0:
            return True

        entries_to_flush = []
        for entry in self.current_chunk:
            entries_to_flush.append(entry.to_list())

        term_bank_number = self._get_next_term_bank_number()
        output_file = os.path.join(self.output_path, f"term_bank_{term_bank_number}.json")

        try:
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(entries_to_flush, out_file, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to write chunk: {output_file}: {e}")
            raise

        self.current_chunk = []

        return True


    def _get_next_term_bank_number(self) -> int:
        if not os.path.isdir(self.output_path):
            raise ValueError(f"Folder {self.output_path} does not exist")

        max_number = 0
        for file in os.listdir(self.output_path):
            match = self.termbank_pattern.match(file)
            if not match:
                continue

            try:
                number = int(match.group(2))
                max_number = max(max_number, number)
            except ValueError:
                raise ValueError(f"Failed to extract term bank number with regex: {file}, Number: {match.group(2)}")

        return max_number + 1


    def _export_index(self, output_path: str) -> bool:
        pass


    def export(self) -> bool:
        if len(self.current_chunk) != 0 and not self._flush_chunk_to_disk():
            raise Exception("Failed to flush remaining entries during export")

        # TODO: export index from config
        return True