# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SignalDrift is a sophisticated sports betting arbitrage and market-making system that combines:
1. **Market Making**: Uses weighted average "fair odds" from sharp sportsbooks to make markets on exchanges
2. **+EV Trading**: Identifies and exploits pricing discrepancies across different platforms including prediction markets

## Common Development Commands

### Environment Setup
```bash
# Mac/Linux
make build      # Creates virtual environment and installs dependencies
make setup      # Alias for build (backwards compatibility)
make start      # Starts Jupyter notebook server (full project access)
make notebooks  # Starts Jupyter notebook server (restricted to /notebooks directory)
make test       # Runs all tests using pytest

# Clean environment
make clean      # Removes venv, __pycache__, and .ipynb_checkpoints
```

### Running Analysis
```bash
# Activate virtual environment first
source venv/bin/activate

# Start Jupyter for interactive analysis
jupyter notebook

# Run specific notebooks
jupyter nbconvert --execute notebooks/market_price.ipynb
```

## Architecture Overview

### Core Strategy (notes/20250601-meeting.md)
Create a weighted average of no-vig odds from sharp sportsbooks (FanDuel, Betfair, Circa, Pinnacle) to serve as a fair market price for market making on exchanges, while simultaneously identifying arbitrage opportunities across platforms including Polymarket.

### Current System Components

1. **Odds Calculators** (`src/calculators/`)
   - American odds conversion utilities
   - Decimal odds conversion utilities
   - Fractional odds conversion utilities
   - All converters handle edge cases and include comprehensive tests

2. **Web Scrapers** (`src/scrapers/`)
   - Betfair scraper with saved page data
   - FanDuel scraper with Chrome profile support
   - Pinnacle scraper implementation
   - Each scraper has test files and sample data

3. **Services** (`src/services/`)
   - Polymarket service for API integration
   - Configuration management with environment variables

4. **Models** (`src/models/`)
   - Market probability calculations
   - Data models for odds and trading

5. **Utilities** (`src/utils/`)
   - Periodic task executor for scheduled jobs

### Current Development Status
- **src/**: Main source code with calculators, scrapers, services, and models
- **notebooks/**: Jupyter notebooks for analysis, experimentation, and data visualization
- **notes/**: Strategic documentation including meeting notes and development plans
- **tests/**: Comprehensive test suite for all components

### Environment Configuration
The project uses `.env` files for configuration. Key variables include:
- `POLYMARKET_API_KEY`: For Polymarket API access
- `PROXY_USERNAME/PASSWORD/HOST/PORT`: Proxy configuration
- `FANDUEL_API_KEY`, `BETFAIR_API_KEY`, `PINNACLE_API_KEY`: Sportsbook APIs
- See `src/config.py` for complete configuration management

### Next Development Steps (from notes/20250601-meeting.md)

#### Priority 1: Foundation
1. Start with data collection - Get basic API connections working for 2-3 sources
2. Build core odds conversion utilities - Essential foundation component ✓ (Completed)
3. Create simple arbitrage detector - Test with manual trades first

#### Priority 2: Optimization
4. Measure and optimize latency - Critical for competitive success
5. Implement basic risk management - Position sizing and exposure limits
6. Build monitoring and alerting - System health and opportunity notifications

## Key Dependencies

- **py-clob-client**: Polymarket API integration
- **pandas/numpy**: Data analysis and calculations
- **matplotlib**: Visualization
- **jupyter**: Interactive development environment
- **selenium**: Web scraping capabilities
- **beautifulsoup4**: HTML parsing for scrapers
- **plotly/ipywidgets**: Interactive visualizations
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework

## Development Notes

1. The project is transitioning from historical analysis to real-time trading system
2. Latency is critical - must achieve sub-second opportunity detection and execution
3. Initial target markets: MLB, NFL, NBA, major soccer leagues
4. Weighted fair value calculation is core to both market making and arbitrage strategies
5. All scrapers save page data locally for testing and development