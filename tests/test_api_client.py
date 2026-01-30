"""
API Client Tests
TDD tests for moltbook REST API wrapper
"""
from unittest.mock import Mock, patch
import json


def test_includes_authorization_header():
    """Given any request, should include Authorization header from credentials"""
    from api_client import MoltbookClient
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="test_key_123")
        client.get("/posts")
        
        # Verify Authorization header was included
        call_args = mock_requests.request.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key_123"


def test_always_uses_www_url():
    """Given www vs non-www URL, should always use www.moltbook.com"""
    from api_client import MoltbookClient
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="test_key")
        client.get("/posts")
        
        # Verify URL uses www
        call_args = mock_requests.request.call_args
        url = call_args.kwargs.get("url", call_args.args[1] if len(call_args.args) > 1 else "")
        assert "www.moltbook.com" in url


def test_401_reports_authentication_error():
    """Given 401 response, should report authentication error"""
    from api_client import MoltbookClient, AuthenticationError
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="bad_key")
        
        try:
            client.get("/posts")
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError as e:
            assert "401" in str(e) or "auth" in str(e).lower()


def test_429_reports_rate_limit():
    """Given 429 response, should report rate limit with retry_after"""
    from api_client import MoltbookClient, RateLimitError
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "Rate limited"}
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="test_key")
        
        try:
            client.get("/posts")
            assert False, "Should have raised RateLimitError"
        except RateLimitError as e:
            assert e.retry_after == 60 or "60" in str(e)


def test_successful_response_returns_data():
    """Given successful response, should parse JSON and return data"""
    from api_client import MoltbookClient
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "posts": [{"id": "123", "title": "Test"}]
        }
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="test_key")
        result = client.get("/posts")
        
        assert result["success"] == True
        assert len(result["posts"]) == 1
        assert result["posts"][0]["id"] == "123"


def test_post_request_sends_json_body():
    """Given POST request with data, should send as JSON body"""
    from api_client import MoltbookClient
    
    with patch('api_client.requests') as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"success": True, "id": "new_post"}
        mock_requests.request.return_value = mock_response
        
        client = MoltbookClient(api_key="test_key")
        result = client.post("/posts", data={"title": "New Post", "content": "Hello"})
        
        call_args = mock_requests.request.call_args
        assert call_args.kwargs.get("json") == {"title": "New Post", "content": "Hello"}


if __name__ == "__main__":
    tests = [
        test_includes_authorization_header,
        test_always_uses_www_url,
        test_401_reports_authentication_error,
        test_429_reports_rate_limit,
        test_successful_response_returns_data,
        test_post_request_sends_json_body,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
