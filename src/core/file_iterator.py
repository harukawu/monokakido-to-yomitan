import os
from typing import List, Tuple


class FileIterator:

    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self._validate_path()
        self.current_index = 0
        self.all_files = []
        for filename in os.listdir(self.directory_path):
            if os.path.isfile(os.path.join(self.directory_path, filename)) and filename.endswith(".xml"):
                self.all_files.append(filename)

            if os.path.isfile(os.path.join(self.directory_path, filename)) and filename.endswith(".json"):
                self.all_files.append(filename)


    def _validate_path(self):
        if not os.path.isdir(self.directory_path):
            raise FileNotFoundError(f'{self.directory_path} is not a directory')

        return True


    def get_next_batch(self, batch_size: int) -> List[Tuple[str, str]]:
        batch = []

        end_index = min(self.current_index + batch_size, len(self.all_files))
        for i in range(self.current_index, end_index):
            file_content = self.read_file(self.all_files[i])
            batch.append((self.all_files[i], file_content))

        self.current_index = end_index
        return batch


    def has_more(self) -> bool:
        return self.current_index < len(self.all_files)


    def get_total_files_count(self) -> int:
        return len(self.all_files)


    def read_file(self, filename: str) -> str:
        result = ""

        file_path = os.path.join(self.directory_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            result = content

        except FileNotFoundError:
            print(f'{self.directory_path}/{filename} is not a file')

        return result
