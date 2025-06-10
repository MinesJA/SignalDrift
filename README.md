# SignalDrift
SignalDrift is a collection of sports betting algorithimic trading strategies.

## Strategies

### Fair Odds Weighted Average Strategy
We use the weighted average "fair odds" from sharp sportsbooks and use that to make trades on open exchanges.

> Hypothesis:
> The average "fair odds" will be a leading indicator of where the price is going on open exchanges

## Environment Setup

### Setting up Environment Variables

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in your credentials** in `.env`:
   ```env
   POLYMARKET_API_KEY=your_actual_api_key
   PROXY_USERNAME=your_nordvpn_username
   # ... etc
   ```

### Usage in Code

#### Method 1: Using the Config Class (Recommended)
```python
from src.config import config

# Access any environment variable
api_key = config.POLYMARKET_API_KEY
proxy_url = config.get_proxy_url()
```

#### Method 2: Direct Access
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('POLYMARKET_API_KEY')
```

### For Jupyter Notebooks

Add this at the top of notebooks:
```python
from dotenv import load_dotenv
load_dotenv()

# Or use the config directly
from src.config import config
```

### Security Best Practices

- Always use `.env` for local development
- Use `.env.example` as a template - commit this file
- Never hardcode secrets in code
- Validate required variables at startup:
  ```python
  from src.config import Config
  Config.validate()  # Raises error if missing required vars
  ```

## Quick Start

### Running

### Running Jupyter Notebook
All Jupyter Notebooks can be found in the `/notebooks` directory.

#### For Mac/Linux Users:
1. Open Terminal
2. Navigate to this directory
3. Run: `make setup`
4. Once setup is complete:
   - Run `make notebooks` to start Jupyter restricted to the `/notebooks` directory only

#### For Windows Users:
1. Open Command Prompt
2. Navigate to this directory
3. Double-click `setup.bat`
4. Once setup is complete, double-click `start.bat`

### Requirements
- Python 3.7 or higher
- Internet connection (for first-time setup)

### Troubleshooting
If you encounter any issues:
1. Make sure Python is installed on your system
2. Try running `make clean` and then `make setup` again
3. Check that you have an active internet connection

### Additional Information
- The setup script will create a virtual environment and install all required packages
- Jupyter notebook will open in your default web browser
- To stop the notebook server, press Ctrl+C in the terminal/command prompt
