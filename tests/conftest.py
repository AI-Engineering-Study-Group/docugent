import pytest
from unittest.mock import MagicMock, patch
import json
from app.services.redis_service import RedisService

@pytest.fixture
def mock_redis_client():
    """Fixture to mock the Redis client."""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.ping.return_value = True
    mock_client.info.return_value = {"redis_version": "6.2.5"}
    mock_client.flushdb.return_value = 10
    return mock_client

@pytest.fixture
def redis_service(mock_redis_client):
    """Fixture to get a RedisService instance with a mocked client."""
    with patch('redis.from_url', return_value=mock_redis_client):
        if RedisService._instance:
            RedisService._instance = None
        service = RedisService.get_instance()
        service.client = mock_redis_client
        yield service
        RedisService._instance = None

@pytest.fixture
def mock_csv_data():
    """Fixture to provide mock CSV data."""
    return [{"id": 1, "name": "Test Session"}]

@pytest.fixture
def mock_load_csv(mock_csv_data):
    """Fixture to mock the _load_csv_data function's file reading part."""
    with patch('app.agents.tools.csv_schedule_tools._load_csv_data') as mock_load:
        mock_load.return_value = mock_csv_data
        yield mock_load
