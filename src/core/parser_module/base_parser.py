from abc import ABC
from typing import List, Tuple
from tqdm import tqdm

from config import DictionaryConfig
from core.file_iterator import FileIterator

class BaseParser(ABC):
    def __init__(self, config: DictionaryConfig, batch_size = 1000) -> None:
        self.config = config
        self.file_iterator = FileIterator(config.dict_path)
        self.files_processed = 0
        self.entries_processed = 0
        self.batch_size = batch_size
        self.bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"


    def parse(self) -> int:
        total_files = self.file_iterator.get_total_files_count()

        self.initialize_processing()

        #count = 0
        with tqdm(total=total_files, desc="進歩", bar_format=self.bar_format, unit="事項") as pbar:
            while self.file_iterator.has_more():
            #while count <= 20:
                batch = self.file_iterator.get_next_batch(self.batch_size)
                self.entries_processed += self._process_batch(batch)
                self.files_processed += self.batch_size
                pbar.update(self.batch_size)
                #count += 1

        self.finalize_processing()

        return total_files


    def initialize_processing(self):
        pass


    def finalize_processing(self):
        pass


    def _process_file(self, filename: str, file_content: str) -> int:
        pass


    def _process_batch(self, batch: List[Tuple[str, str]]) -> int:
        batch_entries_processed = 0

        for filename, file_content in batch:
            entries_from_file = self._process_file(filename, file_content)
            #if entries_from_file == 0:
                #print(f"No entries were processed for file: {filename}")

            batch_entries_processed += entries_from_file

        return batch_entries_processed
