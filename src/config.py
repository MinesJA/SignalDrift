"""Configuration management for SignalDrift."""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
# Looks for .env in the project root directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Central configuration class for all settings."""
    
    # Polymarket Configuration
    POLYMARKET_API_KEY: Optional[str] = os.getenv('POLYMARKET_API_KEY')
    POLYMARKET_PRIVY_TOKEN: Optional[str] = os.getenv('POLYMARKET_PRIVY_TOKEN')
    POLYMARKET_PRIVY_ID_TOKEN: Optional[str] = os.getenv('POLYMARKET_PRIVY_ID_TOKEN')
    POLYMARKET_PRIVATE_KEY: Optional[str] = os.getenv('POLYMARKET_PRIVATE_KEY')
    POLYMARKET_PROXY_ADDRESS: Optional[str] = os.getenv('POLYMARKET_PROXY_ADDRESS')
    
    # API Base URLs
    POLYMARKET_GAMMA_API: str = os.getenv('POLYMARKET_GAMMA_API', 'https://gamma-api.polymarket.com')
    POLYMARKET_CLOB_API: str = os.getenv('POLYMARKET_CLOB_API', 'https://clob.polymarket.com')
    POLYMARKET_WEBSOCKET_URL: str = os.getenv('POLYMARKET_WEBSOCKET_URL', 'wss://ws-subscriptions-clob.polymarket.com')
    
    # Proxy Configuration
    PROXY_USERNAME: Optional[str] = os.getenv('PROXY_USERNAME')
    PROXY_PASSWORD: Optional[str] = os.getenv('PROXY_PASSWORD')
    PROXY_HOST: Optional[str] = os.getenv('PROXY_HOST')
    PROXY_PORT: Optional[str] = os.getenv('PROXY_PORT')
    
    # Sportsbook API Keys
    FANDUEL_API_KEY: Optional[str] = os.getenv('FANDUEL_API_KEY')
    BETFAIR_API_KEY: Optional[str] = os.getenv('BETFAIR_API_KEY')
    PINNACLE_API_KEY: Optional[str] = os.getenv('PINNACLE_API_KEY')
    
    # Application Settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Cookie configurations loaded from YAML files
    FANDUEL_COOKIES: List[Dict[str, Any]] = []
    
    @classmethod
    def load_cookies_from_yaml(cls, yaml_file: str) -> List[Dict[str, Any]]:
        """Load cookies from a YAML file."""
        yaml_path = Path(__file__).parent.parent / yaml_file
        try:
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    return data.get('cookies', [])
            else:
                print(f"Warning: Cookie file {yaml_file} not found at {yaml_path}")
                return []
        except Exception as e:
            print(f"Error loading cookies from {yaml_file}: {e}")
            return []
    
    @classmethod
    def get_proxy_url(cls) -> Optional[str]:
        """Construct proxy URL from components."""
        if all([cls.PROXY_USERNAME, cls.PROXY_PASSWORD, cls.PROXY_HOST, cls.PROXY_PORT]):
            return f"http://{cls.PROXY_USERNAME}:{cls.PROXY_PASSWORD}@{cls.PROXY_HOST}:{cls.PROXY_PORT}"
        return None
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        required = []
        
        # Add your required fields here
        # Example: required = ['POLYMARKET_API_KEY', 'PROXY_USERNAME']
        
        missing = [field for field in required if not getattr(cls, field)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


# Create a convenience instance and load cookies
config = Config()

# Load FanDuel cookies from YAML file
config.FANDUEL_COOKIES = config.load_cookies_from_yaml('fanduel_cookies.yml')