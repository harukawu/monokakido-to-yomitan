import yaml
import importlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class DictionaryConfig:
    """Configuration for dictionary processing"""
    dict_name: str
    rev_name: str
    dict_type: str
    parser_module: str
    parser_class_name: str
    link_strategy_module: str = "strategies.link"
    image_strategy_module: str = "strategies.image"
    normalization_strategy_module: str = "strategies.normalization"
    pos_tags_strategy_module: str = "strategies.pos_tag"
    link_strategy_class: str = "DefaultLinkHandlingStrategy"
    image_strategy_class: str = "DefaultImageHandlingStrategy"
    normalization_strategy_class: str = "DefaultNormalizationStrategy"
    pos_tag_strategy_class: str = "DefaultPosTagStrategy"
    
    # Paths
    dict_path: Optional[str] = None
    index_path: Optional[str] = None
    jukugo_index_path: Optional[str] = None
    idiom_index_path: Optional[str] = None
    kanji_index_path: Optional[str] = None
    jmdict_path: Optional[str] = None
    audio_path: Optional[str] = None
    appendix_entries_path: Optional[str] = None
    tag_map_path: Optional[str] = None
    image_map_path: Optional[str] = None
    output_path: Optional[str] = None
    term_bank_folder: Optional[str] = None
    
    # Optional features
    ignored_elements: Optional[Dict] = None
    expression_element: Optional[str] = None
    has_appendix: bool = False
    appendix_handler_module: Optional[str] = None
    appendix_handler_class: Optional[str] = None
    use_index: bool = True
    use_jmdict: bool = True
    has_audio: bool = False
    parse_all_links: bool = False
    subitems_not_split: bool = False

    # Normalization
    normalization_tag_name: Optional[str] = None
    normalization_class_name: Optional[str] = None
    
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DictionaryConfig':
        """Create DictionaryConfig from dictionary"""
        return cls(**data)
    
    @classmethod
    def load_configs(cls, config_path: str) -> dict[str, 'DictionaryConfig']:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
        return {
            name: cls.from_dict(config)
            for name, config in config_data['dictionaries'].items()
        }
        
    def set_paths(self, paths: dict):
        self.dict_path = paths.get("dict_path")
        self.term_bank_folder = paths.get("term_bank_folder")
        if self.use_index and "index_path" in paths:
            self.index_path = paths.get("index_path")
            self.jukugo_index_path = paths.get("jukugo_index_path")
            self.idiom_index_path = paths.get("idiom_index_path")
            self.kanji_index_path = paths.get("kanji_index_path")
        if self.use_jmdict and "jmdict_path" in paths:
            self.jmdict_path = paths.get("jmdict_path")
        if self.has_audio and "audio_path" in paths:
            self.jmdict_path = paths.get("audio_path")
            
    def validate_required_paths(self):
        required = {
            "dict_path": self.dict_path
        }
        
        if self.use_index:
            required["index_path"] = self.index_path
            self.jukugo_index_path = self.jukugo_index_path if Path(self.jukugo_index_path).exists() else None
            self.idiom_index_path = self.idiom_index_path if Path(self.idiom_index_path).exists() else None
            self.kanji_index_path = self.kanji_index_path if Path(self.kanji_index_path).exists() else None
        if self.use_jmdict:
            required["jmdict_path"] = self.jmdict_path
        if self.has_audio:
            required["audio_path"] = self.audio_path
            
        missing = [name for name, path in required.items() if not path]
        if missing:
            raise ValueError(
                f"Missing required paths for {self.dict_name}: {', '.join(missing)}"
            )
            
    def get_parser_class(self):
        module = importlib.import_module(self.parser_module)
        return getattr(module, self.parser_class_name)
    
    def create_link_strategy(self):
        module = importlib.import_module(self.link_strategy_module)
        strategy_class = getattr(module, self.link_strategy_class)
        return strategy_class()
    
    def create_image_strategy(self):
        module = importlib.import_module(self.image_strategy_module)
        strategy_class = getattr(module, self.image_strategy_class)
        return strategy_class(self.image_map_path) if self.image_map_path else strategy_class()

    def create_normalization_strategy(self):
        module = importlib.import_module(self.normalization_strategy_module)
        strategy_class = getattr(module, self.normalization_strategy_class)
        return strategy_class(self.normalization_tag_name, self.normalization_class_name)

    def create_pos_tags_strategy(self):
        module = importlib.import_module(self.pos_tags_strategy_module)
        strategy_class = getattr(module, self.pos_tag_strategy_class)
        return strategy_class(self.jmdict_path) if self.use_jmdict and self.jmdict_path else strategy_class()
    
    def create_appendix_handler(self, dictionary, directory_path):
        from handlers.appendix_handler import AppendixHandler
        from utils.file_utils import FileUtils
        
        # Load mappings if provided
        tag_mapping = {}
        appendix_entries = {}
        
        if self.tag_map_path:
            tag_mapping = FileUtils.load_json(self.tag_map_path)
            
        if self.appendix_entries_path:
            appendix_entries = FileUtils.load_json(self.appendix_entries_path)
            
        return AppendixHandler(
            dictionary=dictionary,
            directory_path=directory_path,
            tag_mapping=tag_mapping,
            appendix_entries=appendix_entries,
            link_strategy=self.create_link_strategy(),
            image_strategy=self.create_image_strategy(),
            ignored_elements=self.ignored_elements
        )