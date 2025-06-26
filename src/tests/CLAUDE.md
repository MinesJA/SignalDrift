# Testing Documentation for SignalDrift

This document provides guidance for running and managing tests in the SignalDrift project.

## Test Structure

The test suite is organized in a parallel structure to the main source code:

```
src/
├── calculators/          # Odds conversion utilities
├── models/              # Data models and business logic
├── scrapers/            # Web scrapers for sportsbooks
├── services/            # API services and integrations
└── tests/               # Test suite (mirrors src/ structure)
    ├── calculators/     # Tests for odds converters
    ├── models/          # Tests for data models
    ├── scrapers/        # Tests for web scrapers
    └── services/        # Tests for API services
```

## Running Tests

### Make Commands

The project uses a Makefile with convenient test commands:

```bash
# Run all tests
make test

# Run a specific test file (without .py extension)
make test FILE=test_order_book_store

# Run tests for a specific module/directory
make test FILE=models/

# Run with verbose output
make test ARGS="-v"

# Run with coverage report
make test ARGS="--cov=src"
```

### Direct pytest Commands

You can also run pytest directly from the project root:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest src/tests/models/test_order_book_store.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_lookup"

# Run with coverage
pytest --cov=src
```

## Test Categories

### Unit Tests
- **Location**: All test files
- **Purpose**: Test individual functions and methods in isolation
- **Naming**: `test_*.py` files with `test_*` methods
- **Dependencies**: Use mocks/fixtures to isolate components

### Integration Tests
- **Location**: Mixed with unit tests (planned: separate integration/ directory)
- **Purpose**: Test component interactions
- **Examples**: API integration tests, scraper end-to-end tests

### Test Fixtures
- **Location**: `conftest.py` files (project-wide) or within test classes
- **Purpose**: Reusable test data and setup
- **Examples**: Mock objects, sample data, database connections

## Writing New Tests

### Test File Naming Convention
- Test files should be named `test_<module_name>.py`
- Place in the same directory structure as the module being tested
- Example: `src/models/order.py` → `src/tests/models/test_order.py`

### Test Class Structure
```python
import pytest
from unittest.mock import Mock, patch
from src.models.your_module import YourClass

class TestYourClass:
    
    @pytest.fixture
    def sample_instance(self):
        """Create a sample instance for testing."""
        return YourClass(param1="value1", param2="value2")
    
    def test_initialization(self):
        """Test class initialization."""
        instance = YourClass(param1="test")
        assert instance.param1 == "test"
    
    def test_method_behavior(self, sample_instance):
        """Test specific method behavior."""
        result = sample_instance.method_name()
        assert result == expected_value
    
    def test_error_conditions(self, sample_instance):
        """Test error handling."""
        with pytest.raises(ValueError):
            sample_instance.method_that_should_fail()
```

### Best Practices

1. **Use Descriptive Test Names**
   - `test_lookup_returns_correct_book()` not `test_lookup()`
   - Test names should describe the behavior being tested

2. **Follow AAA Pattern**
   - **Arrange**: Set up test data and conditions
   - **Act**: Execute the code being tested  
   - **Assert**: Verify the results

3. **Use Fixtures for Common Setup**
   - Create reusable test data with `@pytest.fixture`
   - Keep fixtures focused and single-purpose

4. **Mock External Dependencies**
   - Use `unittest.mock.Mock` for external services
   - Mock at the boundary of your system
   - Don't mock the system under test

5. **Test Edge Cases**
   - Empty inputs, null values, boundary conditions
   - Error conditions and exception handling
   - Performance edge cases (large datasets, timeouts)

## Test Data Management

### Sample Data Location
- Store test data files in `src/tests/data/`
- Use realistic but anonymized data
- Keep files small and focused

### Environment Variables
- Use separate `.env.test` for test configuration
- Never commit real API keys or credentials
- Use mock services when possible

## Common Test Patterns

### Testing Classes with Dependencies
```python
@pytest.fixture
def mock_dependencies(self):
    """Mock external dependencies."""
    with patch('src.services.api_client.ApiClient') as mock_client:
        yield mock_client

def test_with_mocked_dependencies(self, mock_dependencies):
    """Test behavior with mocked dependencies."""
    service = YourService()
    result = service.method_using_api()
    mock_dependencies.call_api.assert_called_once()
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_async_method(self):
    """Test asynchronous method."""
    result = await async_function()
    assert result == expected_value
```

### Testing Data Models
```python
def test_model_serialization(self):
    """Test model converts to/from dict correctly."""
    model = DataModel(field1="value1", field2=42)
    data_dict = model.to_dict()
    
    assert data_dict["field1"] == "value1"
    assert data_dict["field2"] == 42
    
    # Test deserialization
    restored_model = DataModel.from_dict(data_dict)
    assert restored_model.field1 == model.field1
```

## Debugging Tests

### Running Individual Tests
```bash
# Run single test method
pytest src/tests/models/test_order_book_store.py::TestOrderBookStore::test_lookup

# Run with debugger
pytest --pdb src/tests/models/test_order_book_store.py

# Run with verbose output and no capture (see print statements)
pytest -v -s src/tests/models/test_order_book_store.py
```

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check PYTHONPATH includes project root
   - Verify all dependencies are installed

2. **Mock/Patch Issues**
   - Use correct import path for patching
   - Patch where the object is used, not where it's defined
   - Reset mocks between tests if needed

3. **Fixture Scope Issues**
   - Use appropriate fixture scope (function, class, module, session)
   - Be careful with mutable fixtures

## Test Coverage

### Generating Coverage Reports
```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=src --cov-report=term-missing
```

### Coverage Goals
- Aim for >90% code coverage
- Focus on critical business logic
- Don't sacrifice test quality for coverage percentage
- Exclude trivial code (getters, simple properties) if needed

## Continuous Integration

### Pre-commit Hooks
Tests run automatically before commits. To run manually:
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run only tests
pre-commit run pytest
```

### GitHub Actions
Tests run on every push and pull request. Check status at:
- GitHub Actions tab in repository
- PR status checks
- Commit status indicators

## Performance Testing

### Timing Critical Functions
```python
import time
import pytest

def test_function_performance():
    """Test function completes within time limit."""
    start_time = time.time()
    result = expensive_function()
    end_time = time.time()
    
    assert end_time - start_time < 1.0  # Must complete in <1 second
    assert result is not None

@pytest.mark.slow
def test_comprehensive_performance():
    """Mark slow tests for optional execution."""
    # Comprehensive performance test
    pass
```

### Running Performance Tests
```bash
# Skip slow tests by default
pytest -m "not slow"

# Run only slow tests
pytest -m "slow"

# Run all tests including slow ones
pytest
```

## Test Documentation

### Docstrings in Tests
```python
def test_complex_scenario(self):
    """
    Test complex arbitrage calculation scenario.
    
    Given:
        - Multiple sportsbooks with different odds
        - Varying liquidity conditions
        - Market volatility
    
    When:
        - Arbitrage opportunity is detected
        - Orders are placed simultaneously
    
    Then:
        - Profit calculation is accurate
        - Risk limits are respected
        - Orders execute within latency requirements
    """
```

### Test Planning Documentation
For complex features, create test plans:
- `src/tests/docs/test_plan_arbitrage.md`
- Document test scenarios, edge cases, performance requirements
- Link to business requirements and acceptance criteria