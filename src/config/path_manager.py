from pathlib import Path
from typing import Optional

from config import DictionaryConfig

class PathManager:
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize path manager with optional base directory override"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        
    def get_paths(self, config: DictionaryConfig):
        """Generate all required paths for a dictionary config"""
        dict_type = config.dict_type
        
        paths = {
            "base_dir": self.base_dir,
            "dict_path": self.base_dir / f"resources/{dict_type}/pages",
            "output_path": self.base_dir / "converted",
            "term_bank_folder": self.base_dir / "converted" / config.dict_name,
            "assets_folder": self.base_dir / f"resources/{dict_type}/assets",
            "index_json_path": self.base_dir / f"resources/{dict_type}/index/index.json"
        }
            
        if config.use_index:
            paths["index_path"] = self.base_dir / f"resources/{dict_type}/index/index_d.tsv"
            paths["jukugo_index_path"] = self.base_dir / f"resources/{dict_type}/index/jyukugo_prefix.tsv"
            paths["idiom_index_path"] = self.base_dir / f"resources/{dict_type}/index/idiom_prefix.tsv"
            paths["kanji_index_path"] = self.base_dir / f"resources/{dict_type}/index/kanji_prefix.tsv"
            
        if config.use_jmdict:
            paths["jmdict_path"] = self.base_dir / "resources/JMDICT"
            
        if config.has_audio:
            paths["audio_path"] = self.base_dir / f"resources/{dict_type}/audio/index.json"
            
        if config.has_appendix:
            paths["appendix_path"] = self.base_dir / f"resources/{dict_type}/appendix"
        
        return paths