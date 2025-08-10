import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from app.config.settings import settings

client = TestClient(app)

@pytest.fixture
def mock_redis_service():
    """Fixture to mock the RedisService."""
    with patch('app.services.redis_service.RedisService.get_instance') as mock_get_instance:
        mock_service = MagicMock()
        mock_get_instance.return_value = mock_service
        yield mock_service

def test_invalidate_cache_success(mock_redis_service):
    """Test successful cache invalidation."""
    mock_redis_service.clear_cache.return_value = {"status": "success", "keys_deleted": 10}
    response = client.post(
        "/api/v1/redis/cache/invalidate",
        headers={"X-Secret-Key": settings.secret_key}
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["data"]["status"] == "success"
    assert json_response["message"] == "Cache invalidated successfully"
    mock_redis_service.clear_cache.assert_called_once()

def test_invalidate_cache_unauthorized(mock_redis_service):
    """Test cache invalidation with an invalid secret key."""
    response = client.post(
        "/api/v1/redis/cache/invalidate",
        headers={"X-Secret-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid secret key"
    mock_redis_service.clear_cache.assert_not_called()

def test_invalidate_cache_server_error(mock_redis_service):
    """Test cache invalidation with a server error."""
    mock_redis_service.clear_cache.side_effect = Exception("Redis is down")
    response = client.post(
        "/api/v1/redis/cache/invalidate",
        headers={"X-Secret-Key": settings.secret_key}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to invalidate cache"
    mock_redis_service.clear_cache.assert_called_once()

def test_get_cache_stats_success(mock_redis_service):
    """Test successful retrieval of cache stats."""
    mock_redis_service.get_stats.return_value = {"redis_version": "6.2.5"}
    response = client.get(
        "/api/v1/redis/cache/stats",
        headers={"X-Secret-Key": settings.secret_key}
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["data"]["redis_version"] == "6.2.5"
    assert json_response["message"] == "Cache stats retrieved successfully"
    mock_redis_service.get_stats.assert_called_once()

def test_get_cache_stats_unauthorized(mock_redis_service):
    """Test retrieval of cache stats with an invalid secret key."""
    response = client.get(
        "/api/v1/redis/cache/stats",
        headers={"X-Secret-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid secret key"
    mock_redis_service.get_stats.assert_not_called()

def test_get_cache_stats_server_error(mock_redis_service):
    """Test retrieval of cache stats with a server error."""
    mock_redis_service.get_stats.side_effect = Exception("Redis is down")
    response = client.get(
        "/api/v1/redis/cache/stats",
        headers={"X-Secret-Key": settings.secret_key}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get cache stats"
    mock_redis_service.get_stats.assert_called_once()
