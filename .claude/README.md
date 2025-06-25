# Claude Code GitHub Integration Notes

## Efficient GitHub MCP Workflow for Pull Requests

The GitHub MCP server provides powerful tools for managing branches and pull requests without dealing with local git authentication issues. Here's the most efficient workflow:

### Optimal Workflow for Creating PRs

#### Step 1: Work in a Git Worktree (Recommended)
```bash
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

