# Testing Documentation

This document describes the test coverage for the RAG chatbot system, focusing on source rendering and security.

## Test Setup

### Installing Test Dependencies

The project uses pytest for testing. Install test dependencies with:

```bash
uv add --dev pytest pytest-cov pytest-mock
```

### Running Tests

From the backend directory:

```bash
# Run all tests
cd backend
uv run pytest

# Run with coverage report
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest test_vector_store.py

# Run tests with specific markers
uv run pytest -m xss
```

## Test Coverage

### 1. Backend Tests (`backend/`)

#### `test_vector_store.py` - Lesson Link Retrieval Tests

Tests for `VectorStore.get_lesson_link()` method:

- ✅ **Valid lesson links**: Verifies correct link retrieval for valid lesson numbers
- ✅ **Sources without links**: Ensures None is returned when lesson has no link
- ✅ **Missing courses**: Handles gracefully when course doesn't exist in database
- ✅ **Invalid JSON metadata**: Handles corrupted JSON in metadata without crashing
- ✅ **Missing lesson numbers**: Returns None for non-existent lesson numbers
- ✅ **Exception handling**: Gracefully handles database errors

#### `test_url_validation.py` - XSS Protection Tests

Tests for `is_safe_url()` security function:

- ✅ **Valid HTTP/HTTPS URLs**: Accepts legitimate URLs
- ✅ **JavaScript XSS attempts**: Blocks `javascript:` scheme attacks
- ✅ **Data URI XSS attempts**: Blocks `data:` URI attacks
- ✅ **VBScript attacks**: Blocks `vbscript:` scheme attacks
- ✅ **File URI blocking**: Prevents file:// access attempts
- ✅ **Malformed URLs**: Handles invalid URL formats safely
- ✅ **Case sensitivity**: Handles mixed-case scheme attempts
- ✅ **Special characters**: Accepts valid URLs with encoded characters

#### `test_source_rendering.py` - Source Enhancement Tests

Tests for source preparation logic in `rag_system.py`:

- ✅ **Valid lesson links render correctly**: Ensures proper source enhancement
- ✅ **Sources without links display as plain text**: Validates None link handling
- ✅ **Malformed URLs don't break rendering**: Tests defensive URL handling
- ✅ **XSS attempts are sanitized**: Verifies XSS protection in source data
- ✅ **Missing course handling**: Tests graceful handling of incomplete data
- ✅ **Defensive source validation**: Validates input type checking

### 2. Frontend Tests (Future)

The frontend source rendering logic (`frontend/script.js:126-135`) should be tested with:

**Recommended approach**: Use Jest or Vitest for JavaScript testing

Test scenarios to cover:
- ✅ Sources with valid links render as clickable anchor tags
- ✅ Sources without links render as plain text in divs
- ✅ HTML escaping prevents XSS in source text
- ✅ Links open in new tabs with security attributes
- ✅ Multiple sources display correctly
- ✅ Empty source arrays don't break rendering

Example Jest test structure:

```javascript
// frontend/script.test.js
describe('Source Rendering', () => {
  test('sources with links render as clickable elements', () => {
    const sources = [
      { text: 'Course - Lesson 1', link: 'https://example.com/lesson1' }
    ];
    // Test rendering logic
  });

  test('sources without links display as plain text', () => {
    const sources = [
      { text: 'Course - General', link: null }
    ];
    // Test rendering logic
  });
});
```

## Security Testing

### XSS Prevention

The system implements multiple layers of XSS protection:

1. **Backend URL Validation** (`rag_system.py:11-26`):
   - Validates all URLs before adding to sources
   - Only allows `http://` and `https://` schemes
   - Blocks `javascript:`, `data:`, `file:`, `vbscript:` schemes

2. **Frontend HTML Escaping** (`script.js:153-157`):
   - Uses `escapeHtml()` for all user-controlled text
   - Prevents HTML injection in source text

3. **Link Security Attributes** (`script.js:130`):
   - Uses `rel="noopener noreferrer"` on all links
   - Prevents window.opener attacks

### Testing XSS Scenarios

The test suite covers various XSS attack vectors:

```bash
# Run XSS-specific tests
cd backend
uv run pytest -m xss test_url_validation.py
```

## Test Organization

### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.xss` - Security/XSS tests
- `@pytest.mark.rendering` - Source rendering tests

Use markers to run specific test categories:

```bash
uv run pytest -m unit          # Run only unit tests
uv run pytest -m xss           # Run only security tests
uv run pytest -m rendering     # Run only rendering tests
```

## Coverage Goals

Current backend test coverage targets:

- `vector_store.get_lesson_link()`: 100% coverage
- `rag_system.is_safe_url()`: 100% coverage
- `rag_system.query()` source enhancement: 100% coverage

Frontend test coverage targets (pending):

- `script.js` source rendering: Target 100% coverage
- `escapeHtml()` function: Target 100% coverage

## Continuous Integration

To add tests to CI/CD pipeline, add to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: |
          cd backend
          uv run pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure XSS protection for any user-controlled data
3. Add appropriate test markers
4. Update this documentation with new test descriptions
5. Maintain 100% coverage for security-critical code

## Troubleshooting

### ImportError: No module named 'pytest'

Install test dependencies:
```bash
uv add --dev pytest pytest-cov pytest-mock
```

### ChromaDB connection errors during tests

Use mocking to avoid ChromaDB dependencies in unit tests:
```python
from unittest.mock import Mock, MagicMock
mock_store = Mock(spec=VectorStore)
```

### Tests pass but coverage is low

Generate HTML coverage report to find untested code:
```bash
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html
```
