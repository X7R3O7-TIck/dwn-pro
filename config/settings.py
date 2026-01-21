"""Configuration management"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DownloadConfig:
    """Download configuration"""
    default_quality: str = "best"
    default_format: str = "mp4"
    output_dir: str = "./downloads"
    max_concurrent_downloads: int = 3
    download_timeout: int = 300
    create_subdirectories: bool = True


@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    debug: bool = False
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class Config:
    """Main configuration class"""
    download: DownloadConfig = field(default_factory=DownloadConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment
    
    Args:
        config_file: Path to config file (JSON, YAML, or .env)
        
    Returns:
        Config object
    """
    config = Config()
    
    # Load from environment variables
    _load_from_env(config)
    
    # Load from config file if provided
    if config_file:
        config_file = Path(config_file)
        if config_file.exists():
            if config_file.suffix == '.json':
                _load_from_json(config, config_file)
            elif config_file.suffix in ('.yaml', '.yml'):
                _load_from_yaml(config, config_file)
            elif config_file.name == '.env':
                _load_from_dotenv(config, config_file)
    
    return config


def _load_from_env(config: Config):
    """Load configuration from environment variables"""
    # Download settings
    if 'SMD_DEFAULT_QUALITY' in os.environ:
        config.download.default_quality = os.environ['SMD_DEFAULT_QUALITY']
    if 'SMD_DEFAULT_FORMAT' in os.environ:
        config.download.default_format = os.environ['SMD_DEFAULT_FORMAT']
    if 'SMD_OUTPUT_DIR' in os.environ:
        config.download.output_dir = os.environ['SMD_OUTPUT_DIR']
    if 'SMD_MAX_CONCURRENT' in os.environ:
        config.download.max_concurrent_downloads = int(os.environ['SMD_MAX_CONCURRENT'])
    
    # API settings
    if 'SMD_API_HOST' in os.environ:
        config.api.host = os.environ['SMD_API_HOST']
    if 'SMD_API_PORT' in os.environ:
        config.api.port = int(os.environ['SMD_API_PORT'])
    if 'SMD_API_WORKERS' in os.environ:
        config.api.workers = int(os.environ['SMD_API_WORKERS'])
    if 'SMD_API_DEBUG' in os.environ:
        config.api.debug = os.environ['SMD_API_DEBUG'].lower() == 'true'
    
    # Logging settings
    if 'SMD_LOG_LEVEL' in os.environ:
        config.logging.level = os.environ['SMD_LOG_LEVEL']
    if 'SMD_LOG_FILE' in os.environ:
        config.logging.file = os.environ['SMD_LOG_FILE']


def _load_from_json(config: Config, file_path: Path):
    """Load configuration from JSON file"""
    import json
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'download' in data:
        download_data = data['download']
        config.download.default_quality = download_data.get('default_quality', config.download.default_quality)
        config.download.default_format = download_data.get('default_format', config.download.default_format)
        config.download.output_dir = download_data.get('output_dir', config.download.output_dir)
    
    if 'api' in data:
        api_data = data['api']
        config.api.host = api_data.get('host', config.api.host)
        config.api.port = api_data.get('port', config.api.port)


def _load_from_yaml(config: Config, file_path: Path):
    """Load configuration from YAML file"""
    try:
        import yaml
    except ImportError:
        return
    
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if data:
        if 'download' in data:
            download_data = data['download']
            config.download.default_quality = download_data.get('default_quality', config.download.default_quality)
            config.download.default_format = download_data.get('default_format', config.download.default_format)
            config.download.output_dir = download_data.get('output_dir', config.download.output_dir)
        
        if 'api' in data:
            api_data = data['api']
            config.api.host = api_data.get('host', config.api.host)
            config.api.port = api_data.get('port', config.api.port)


def _load_from_dotenv(config: Config, file_path: Path):
    """Load configuration from .env file"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    
    load_dotenv(file_path)
    _load_from_env(config)


def save_config(config: Config, config_file: str):
    """Save configuration to file"""
    import json
    
    data = {
        'download': {
            'default_quality': config.download.default_quality,
            'default_format': config.download.default_format,
            'output_dir': config.download.output_dir,
            'max_concurrent_downloads': config.download.max_concurrent_downloads,
        },
        'api': {
            'host': config.api.host,
            'port': config.api.port,
            'workers': config.api.workers,
            'debug': config.api.debug,
        },
        'logging': {
            'level': config.logging.level,
            'file': config.logging.file,
        },
    }
    
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=2)


def get_default_config() -> Config:
    """Get default configuration"""
    return Config()


def create_config_file(path: str = "config.json"):
    """Create a sample config file"""
    config = get_default_config()
    save_config(config, path)
    return path
