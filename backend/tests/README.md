# MyCousinVinyl Backend Tests

This directory contains comprehensive tests for the MyCousinVinyl backend application.

## Test Structure

```
tests/
├── unit/                      # Unit tests (no external dependencies)
│   ├── domain/               # Domain entity tests
│   ├── application/          # Application service tests
│   └── adapters/             # Adapter tests (mocked external dependencies)
├── integration/              # Integration tests (require database, etc.)
│   └── test_artist_endpoints.py
├── conftest.py              # Shared pytest fixtures
└── README.md                # This file
```

## Test Types

### Unit Tests
Fast, isolated tests with no external dependencies. Test business logic, validation, and domain rules.

- **Domain Tests**: Test domain entities (Artist, Album, Pressing, etc.)
- **Application Tests**: Test application services with mocked repositories
- **Coverage**: 167 tests

### Integration Tests
Test the full application stack including database, HTTP endpoints, and authentication.

- **API Endpoint Tests**: Test FastAPI routes, request/response handling, authorization
- **Require**: Database connection, installed dependencies

## Running Tests

### Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

### Run Unit Tests Only (Fast)

Unit tests don't require database or external services:

```bash
# Run all unit tests
pytest tests/unit/

# Run domain tests only
pytest tests/unit/domain/

# Run application service tests only
pytest tests/unit/application/

# Run with verbose output
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/domain/test_artist.py

# Run specific test
pytest tests/unit/domain/test_artist.py::TestArtistCreation::test_create_artist_with_valid_data
```

### Run Integration Tests (Require Database)

Integration tests require a running PostgreSQL database:

```bash
# Start test database (Docker)
docker run -d \
  --name mycousinvinyl-test-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mycousinvinyl_test \
  -p 5433:5432 \
  postgres:16

# Run integration tests
pytest tests/integration/ -m integration

# Run all tests (unit + integration)
pytest
```

### Run All Tests

```bash
# Run everything
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run and generate coverage HTML report (opens in browser)
pytest --cov=app --cov-report=html && open htmlcov/index.html
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests (default)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.asyncio` - Async tests (auto-applied by pytest-asyncio)

### Filter by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run everything except slow tests
pytest -m "not slow"
```

## Test Coverage

Current test coverage:

- **Domain Entities**: 143 tests
  - Artist: 47 tests
  - Album: 33 tests
  - Pressing: 36 tests
  - CollectionItem: 27 tests

- **Application Services**: 24 tests
  - ArtistService: 24 tests

- **API Endpoints**: Integration tests available
  - Artist endpoints: Full CRUD + authorization

## Writing New Tests

### Unit Test Example

```python
# tests/unit/domain/test_my_entity.py
import pytest
from uuid import uuid4

from app.domain.entities import MyEntity

class TestMyEntityCreation:
    """Test entity creation."""

    def test_create_with_valid_data(self):
        """Should create entity with valid data."""
        entity = MyEntity(name="Test")
        assert entity.name == "Test"
        assert entity.id is not None

    def test_create_with_invalid_data(self):
        """Should raise error with invalid data."""
        with pytest.raises(ValueError, match="Name is required"):
            MyEntity(name="")
```

### Application Service Test Example

```python
# tests/unit/application/test_my_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.services.my_service import MyService

@pytest.fixture
def mock_uow():
    """Create mock Unit of Work."""
    uow = MagicMock()
    uow.my_repository = AsyncMock()
    uow.commit = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow

@pytest.fixture
def my_service(mock_uow):
    """Create service with mocked UoW."""
    return MyService(uow=mock_uow)

class TestMyService:
    """Test my service."""

    @pytest.mark.asyncio
    async def test_create(self, my_service, mock_uow):
        """Should create entity."""
        # Arrange
        mock_uow.my_repository.add.return_value = MyEntity(id=uuid4(), name="Test")

        # Act
        result = await my_service.create(name="Test")

        # Assert
        assert result.name == "Test"
        mock_uow.my_repository.add.assert_called_once()
        mock_uow.commit.assert_called_once()
```

### Integration Test Example

```python
# tests/integration/test_my_endpoints.py
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.integration

class TestMyEndpoint:
    """Test my API endpoint."""

    @pytest.mark.asyncio
    async def test_create_endpoint(self, client, mock_auth_token, mock_editor_user):
        """Should create via API."""
        with patch("app.entrypoints.http.auth.verify_token", return_value=mock_editor_user):
            response = await client.post(
                "/my-endpoint",
                json={"name": "Test"},
                headers={"Authorization": mock_auth_token}
            )

        assert response.status_code == 201
        assert response.json()["name"] == "Test"
```

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Commits to main branch
- Before deployments

CI configuration: `.github/workflows/test.yml` (if using GitHub Actions)

## Debugging Tests

### Run with debug output

```bash
# Show print statements
pytest -s

# Show detailed failure info
pytest -vv

# Drop into debugger on failure
pytest --pdb

# Run last failed tests only
pytest --lf
```

### Common Issues

1. **"No module named 'sqlalchemy'"**
   - Unit tests don't need SQLAlchemy
   - Integration tests need: `pip install -r requirements.txt`

2. **"Connection refused" errors**
   - Integration tests need running database
   - Start test database with Docker (see above)

3. **Authentication errors in integration tests**
   - Tests mock authentication by default
   - Real Azure AD not needed for tests

## Test Data

Test data is:
- Generated fresh for each test (no shared state)
- Cleaned up after tests complete
- Uses factories/fixtures for consistency

## Best Practices

1. **Keep unit tests fast** - No database, no HTTP calls, no file I/O
2. **Mock external dependencies** - Use `unittest.mock` for repositories, APIs
3. **Test one thing per test** - Clear, focused test cases
4. **Use descriptive names** - Test names should describe what they test
5. **Arrange-Act-Assert pattern** - Clear test structure
6. **Clean up resources** - Use fixtures for setup/teardown
7. **Independent tests** - Tests should not depend on each other

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
