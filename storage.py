# keep as log, pass around file names, maybe move this to the main file and never touch in util files
# other potential GETs can use 

from pathlib import Path
import uuid

STORAGE = Path('./STORAGE')
def new_path(orig_fn: str) -> Path:
    ext = Path(orig_fn).suffix.lower()
    return STORAGE / f'{uuid.uuid4().hex}{ext}'

class Storage:
    def __init__(self, filename):
        self.name = filename
        self.path = new_path(filename)

class ImageStorage(Storage):
    def __init__(self, bytes_data, filename):
        super().__init__(filename)
        self.bytes_data = bytes_data
        self.written = False
    def write(self):
        with open(str(self.path)) as f:
            f.write(self.bytes_data)
        self.written = True