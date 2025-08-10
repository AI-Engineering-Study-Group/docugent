import pytest
from unittest.mock import MagicMock, patch
from app.services.redis_service import RedisService
from app.agents.tools.csv_schedule_tools import _load_csv_data
from app.services.web_scraping_service import WebScrapingService
import redis
import json

class TestRedisService:
    """Test suite for the RedisService."""

    def test_get_instance(self):
        """Test that get_instance returns a singleton instance."""
        instance1 = RedisService.get_instance()
        instance2 = RedisService.get_instance()
        assert instance1 is instance2
        RedisService._instance = None # Clean up singleton

    def test_connection_error(self):
        """Test that RedisService handles connection errors gracefully."""
        with patch('redis.from_url', side_effect=redis.exceptions.ConnectionError):
            service = RedisService()
            assert service.client is None
            RedisService._instance = None # Clean up singleton

    def test_get_item(self, redis_service):
        """Test getting an item from the cache."""
        key = "test_key"
        value = {"data": "test_value"}
        redis_service.client.get.return_value = json.dumps(value)
        
        result = redis_service.get(key)
        
        redis_service.client.get.assert_called_once_with(key)
        assert result == value

    def test_get_item_not_found(self, redis_service):
        """Test getting a non-existent item from the cache."""
        key = "non_existent_key"
        redis_service.client.get.return_value = None
        
        result = redis_service.get(key)
        
        redis_service.client.get.assert_called_once_with(key)
        assert result is None

    def test_set_item(self, redis_service):
        """Test setting an item in the cache."""
        key = "test_key"
        value = {"data": "test_value"}
        ttl = 3600
        
        redis_service.set(key, value, ttl)
        
        redis_service.client.set.assert_called_once_with(key, json.dumps(value), ex=ttl)

    def test_get_stats(self, redis_service):
        """Test getting Redis stats."""
        stats = redis_service.get_stats()
        
        redis_service.client.info.assert_called_once()
        assert stats == {"redis_version": "6.2.5"}

    def test_clear_cache(self, redis_service):
        """Test clearing the cache."""
        result = redis_service.clear_cache()
        
        redis_service.client.flushdb.assert_called_once()
        assert result == {"status": "success", "keys_deleted": 10}

class TestCsvScheduleTools:
    """Test suite for the CSV schedule tools caching."""

    @patch('app.agents.tools.csv_schedule_tools.redis_service')
    def test_load_csv_data_from_file_and_cache(self, mock_redis, mock_csv_data):
        """Test that data is loaded from CSV and cached if not in Redis."""
        mock_redis.get.return_value = None
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            with patch('csv.DictReader', return_value=[{"Title": "Test"}]):
                data = _load_csv_data()
                mock_redis.get.assert_called_once_with("csv_data")
                mock_redis.set.assert_called_once()
                assert data is not None

    @patch('app.agents.tools.csv_schedule_tools.redis_service')
    def test_load_csv_data_from_cache(self, mock_redis, mock_csv_data):
        """Test that data is loaded from cache if available."""
        mock_redis.get.return_value = mock_csv_data
        
        data = _load_csv_data()
        
        mock_redis.get.assert_called_once_with("csv_data")
        mock_redis.set.assert_not_called()
        assert data == mock_csv_data

@pytest.mark.asyncio
class TestWebScrapingService:
    """Test suite for the WebScrapingService caching."""

    @patch('app.services.web_scraping_service.aiohttp.ClientSession')
    async def test_fetch_url_from_web_and_cache(self, mock_session):
        """Test that data is fetched from the web and cached."""
        url = "http://test.com"
        mock_response = MagicMock()
        mock_response.status = 200
        # aiohttp response.text() is a coroutine
        async def mock_text():
            return "<html><body>Test</body></html>"
        mock_response.text = mock_text
        
        # Configure the async context manager
        async def __aenter__(*args, **kwargs):
            return mock_response
        
        async def __aexit__(*args, **kwargs):
            pass

        mock_session.return_value.get.return_value.__aenter__ = __aenter__
        mock_session.return_value.get.return_value.__aexit__ = __aexit__

        with patch('app.services.redis_service.RedisService.get_instance') as mock_get_instance:
            mock_redis_service = MagicMock()
            mock_get_instance.return_value = mock_redis_service
            
            service = WebScrapingService()
            
            mock_redis_service.get.return_value = None
            
            result = await service._fetch_url(url)
            
            mock_redis_service.get.assert_called_once()
            mock_redis_service.set.assert_called_once()
            assert result['cached'] is False

    @patch('app.services.web_scraping_service.aiohttp.ClientSession')
    async def test_fetch_url_from_cache(self, mock_session):
        """Test that data is fetched from the cache."""
        url = "http://test.com"
        cached_data = {"data": "cached_value"}
        
        with patch('app.services.redis_service.RedisService.get_instance') as mock_get_instance:
            mock_redis_service = MagicMock()
            mock_get_instance.return_value = mock_redis_service
            
            service = WebScrapingService()
            
            mock_redis_service.get.return_value = cached_data
            
            result = await service._fetch_url(url)
            
            mock_redis_service.get.assert_called_once()
            mock_redis_service.set.assert_not_called()
            assert result == cached_data
