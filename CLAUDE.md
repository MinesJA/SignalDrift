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
make build                          # Creates virtual environment and installs dependencies
make setup                          # Alias for build (backwards compatibility)
make clean                          # Removes venv, __pycache__, and .ipynb_checkpoints

# IMPORTANT: When starting work on a new issue or branch, always run:
make clean && make build && make test  # Clean environment, rebuild, and run all tests
```

### Running the System
```bash
make start                          # Starts trading system
```

### Jupyter Notebooks
```bash
make notebooks                      # Starts Jupyter notebook server (restricted to /notebooks directory)
make notebooks FILE={notebook_name} # Run a specific notebook (without .ipynb extension)
```

### Testing
```bash
make test                                    # Runs all tests using pytest
make test FILE={test_name}                   # Run a specific test file (without test_ prefix or .py extension)
make test ARGS="{pytest_options}"           # Run all tests with additional pytest options
make test FILE={test_name} ARGS="{options}" # Run specific test with additional options

# Common debugging examples:
make test FILE=test_order_book_store ARGS="-s"           # Disable output capture for breakpoint() debugging
make test FILE=test_order_book_store ARGS="-s --pdb"     # Auto-drop into debugger on failures
make test ARGS="--maxfail=1"                             # Stop after first failure
make test ARGS="-x --tb=short"                           # Stop on first failure with short traceback
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
- **src/tests/**: Comprehensive test suite for all components
- **notebooks/**: Jupyter notebooks for analysis, experimentation, and data visualization
- **notes/**: Strategic documentation including meeting notes and development plans
- **data/**: CSV files with trading data collected while running system

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


# SignalDrift

## Git workflow

### Branch Naming Conventions
Always use descriptive branch names that follow these patterns to ensure easy association with issues and PRs:

#### Standard Patterns
- **Bug fixes**: `fix-{description}-issue{number}` (e.g., `fix-ci-pytest-issue36`)
- **Features**: `feature-{description}-issue{number}` (e.g., `feature-order-placement-issue12`)
- **Refactoring**: `refactor-{component}-issue{number}` (e.g., `refactor-market-dao-issue45`)
- **Documentation**: `docs-{description}-issue{number}` (e.g., `docs-api-guide-issue8`)
- **Testing**: `test-{component}-issue{number}` (e.g., `test-polymarket-service-issue22`)
- **Data cleanup**: `data-cleanup-{description}-issue{number}` (e.g., `data-cleanup-c-issue23`)

#### Key Rules
1. Always include the issue number at the end when working on a specific issue
2. Use hyphens to separate words (no underscores)
3. Keep names concise but descriptive
4. Match the branch type to the primary purpose of the change
5. For PRs without issues, use descriptive names: `fix-{description}` (e.g., `fix-import-error`)

### PR Tracking Best Practices

#### 1. Track PR Information Immediately After Creation
When creating a PR, always document these details in your TODO list:
```
PR #38: Fix CI/CD pytest failures
- Branch: fix-ci-pytest-issue36
- Status: Open
- Build: Failed
- Last Error: SyntaxError in market_dao.py:18
- GitHub Actions Run: 15912229471
```

#### 2. Use Structured TODO Items for PR Tasks
Track all PR-related work items:
- Fix specific errors found in CI/CD
- Update PR after changes
- Monitor build status
- Request reviews when ready

#### 3. Quick PR Lookup Commands
```python
# Find PR by branch name (most reliable)
mcp__github__search_issues(q="repo:MinesJA/SignalDrift is:pr head:fix-ci-pytest-issue36")

# Get PR details by number
mcp__github__get_pull_request(owner="MinesJA", repo="SignalDrift", pullNumber=38)

# Check build status
mcp__github__get_pull_request_status(owner="MinesJA", repo="SignalDrift", pullNumber=38)
```

#### 4. Debug Build Failures Workflow
```bash
# 1. List recent workflow runs
gh run list --repo MinesJA/SignalDrift --limit 5

# 2. View specific run details
gh run view <run-id> --repo MinesJA/SignalDrift

# 3. Get failure logs
gh run view <run-id> --repo MinesJA/SignalDrift --log-failed | tail -50
```

#### 5. Associate Local Work with Remote PRs
- Branch name should match PR head branch
- Include PR number in commit messages: "Fix error (PR #38)"
- Update TODO list with PR numbers as soon as created

## Github Workflow
Always use the GitHub MCP server for all tasks related to Github. That includes:
- Opening Pull requests
- Pulling down project issue details
- Creating project issues
- Pushing to remote branches
- Pulling from remote branches

### Workflow for Creating PRs

#### Step 1: Work in a Git Worktree (Recommended)


```bash
# In the main directory of the project (/SignalDrift),
# and while on the `main` branch, pull down latest changes
git pull

# Create a new worktree for your feature branch
git worktree add ../SignalDrift-feature-name -b feature-name

# Navigate to the worktree
cd ../SignalDrift-feature-name

# Make your changes and commit locally
git add .
git commit -m "Your commit message"
```



#### Step 2: Push Changes Using GitHub MCP
When `git push` fails due to authentication issues, use the MCP tools:

```python
# 1. Get your GitHub username (only needed once per session)
mcp__github__get_me()

# 2. Create the branch on GitHub
mcp__github__create_branch(
    owner="MinesJA",  # or your username
    repo="SignalDrift",
    branch="feature-name",
    from_branch="main"
)

# 3. Push your files directly via API
mcp__github__push_files(
    owner="MinesJA",
    repo="SignalDrift",
    branch="feature-name",
    message="Your commit message",
    files=[
        {"path": "src/file1.py", "content": "file contents..."},
        {"path": "src/file2.py", "content": "file contents..."}
    ]
)

# 4. Create the pull request
mcp__github__create_pull_request(
    owner="MinesJA",
    repo="SignalDrift",
    title="PR Title",
    head="feature-name",
    base="main",
    body="## Summary\n- Change 1\n- Change 2\n\n## Test Results\n..."
)
```

### Best Practices

1. **Always use worktrees** for feature branches to keep main branch clean
2. **Read file contents** before pushing to ensure you're sending the right version
3. **Use descriptive branch names** that match the PR purpose
4. **Include comprehensive PR descriptions** with Summary, Changes, and Test Results sections

### Common MCP Tools for GitHub Workflow

#### Repository Management
- `mcp__github__get_me()` - Get authenticated user info
- `mcp__github__create_branch()` - Create new branches
- `mcp__github__list_branches()` - List existing branches
- `mcp__github__get_file_contents()` - Read files from GitHub

#### Pull Request Management
- `mcp__github__create_pull_request()` - Create new PRs
- `mcp__github__list_pull_requests()` - List existing PRs
- `mcp__github__get_pull_request()` - Get PR details
- `mcp__github__update_pull_request()` - Update PR title/description
- `mcp__github__merge_pull_request()` - Merge approved PRs

#### Code Review
- `mcp__github__create_pending_pull_request_review()` - Start a review
- `mcp__github__add_pull_request_review_comment_to_pending_review()` - Add review comments
- `mcp__github__submit_pending_pull_request_review()` - Submit the review
- `mcp__github__request_copilot_review()` - Request AI code review

### Troubleshooting

#### Error: 422 Validation Failed
- **Cause**: Branch doesn't exist on remote
- **Solution**: Use `mcp__github__create_branch()` first

#### Error: Authentication failed
- **Cause**: Local git credentials issues
- **Solution**: Use MCP tools instead of git push

#### Error: File content mismatch
- **Cause**: Local changes not reflected in push
- **Solution**: Read files with `Read` tool before using `mcp__github__push_files()`

### Complete Example: Bug Fix Workflow

```python
# 1. Create worktree and make changes
# (done via bash commands)

# 2. Create branch on GitHub
mcp__github__create_branch(
    owner="MinesJA",
    repo="SignalDrift",
    branch="fix-polymarket-bug"
)

# 3. Read the modified files
file1_content = Read("src/models/order.py")
file2_content = Read("src/strategies/polymarket_arb.py")

# 4. Push changes
mcp__github__push_files(
    owner="MinesJA",
    repo="SignalDrift",
    branch="fix-polymarket-bug",
    message="Fix polymarket arbitrage detection bug",
    files=[
        {"path": "src/models/order.py", "content": file1_content},
        {"path": "src/strategies/polymarket_arb.py", "content": file2_content}
    ]
)

# 5. Create PR with detailed description
mcp__github__create_pull_request(
    owner="MinesJA",
    repo="SignalDrift",
    title="Fix polymarket arbitrage order CSV writing bug",
    head="fix-polymarket-bug",
    base="main",
    body="""## Summary
- Fixed bug where orders weren't written to CSV
- Root cause: missing market_slug field

## Changes
- Uncommented market_slug in Order model
- Updated strategy to pass market_slug

## Test Results
- Created test confirming fix works
- Orders now write to CSV correctly
"""
)
```

### Advanced Features

#### Batch Operations
The MCP tools support efficient batch operations:
- Push multiple files in one API call
- Create multiple issues/PRs programmatically
- Bulk update PR statuses

#### Integration with CI/CD
- Check PR status with `mcp__github__get_pull_request_status()`
- Monitor checks and tests
- Auto-merge when all checks pass

#### Collaborative Features
- Assign reviewers to PRs
- Add labels and milestones
- Link issues to PRs
- Request specific team reviews


