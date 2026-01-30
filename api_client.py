"""
API Client
Wrapper for moltbook REST API with authentication and error handling.
Always uses www.moltbook.com to avoid redirect issues.
"""
import requests
from typing import Any, Dict, Optional
from dataclasses import dataclass


# Base URL - ALWAYS use www to avoid redirects
BASE_URL = "https://www.moltbook.com/api/v1"


class MoltbookError(Exception):
    """Base exception for moltbook API errors."""
    pass


class AuthenticationError(MoltbookError):
    """Raised when API returns 401 Unauthorized."""
    pass


class RateLimitError(MoltbookError):
    """Raised when API returns 429 Too Many Requests."""
    
    def __init__(self, message: str, retry_after: int = 0):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(MoltbookError):
    """Raised when API returns 404 Not Found."""
    pass


class MoltbookClient:
    """REST API client for moltbook.com."""
    
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        """
        Initialize client.
        
        Args:
            api_key: Moltbook API key for authentication
            base_url: API base URL (defaults to www.moltbook.com)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Clawdbot-MoltbookSkill/1.0"
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response, raising appropriate exceptions.
        
        Args:
            response: Response from requests
            
        Returns:
            Parsed JSON data
            
        Raises:
            AuthenticationError: On 401
            RateLimitError: On 429
            NotFoundError: On 404
            MoltbookError: On other errors
        """
        if response.status_code == 401:
            raise AuthenticationError(
                f"Authentication failed (401): Invalid or expired API key"
            )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Rate limited (429): Retry after {retry_after} seconds",
                retry_after=retry_after
            )
        
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found (404)")
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("error", f"API error: {response.status_code}")
            except:
                message = f"API error: {response.status_code}"
            raise MoltbookError(message)
        
        return response.json()
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an API request.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., /posts)
            data: JSON body for POST/PUT requests
            params: Query parameters
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            json=data,
            params=params,
            timeout=30
        )
        
        return self._handle_response(response)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint)
    
    # === Convenience Methods ===
    
    def get_feed(self, sort: str = "hot", limit: int = 25) -> Dict[str, Any]:
        """Get the main feed."""
        return self.get("/posts", params={"sort": sort, "limit": limit})
    
    def get_submolt(self, name: str, limit: int = 25) -> Dict[str, Any]:
        """Get posts from a specific submolt."""
        return self.get(f"/submolts/{name}", params={"limit": limit})
    
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a single post with comments."""
        return self.get(f"/posts/{post_id}")
    
    def upvote(self, post_id: str) -> Dict[str, Any]:
        """Upvote a post."""
        return self.post(f"/posts/{post_id}/upvote")
    
    def downvote(self, post_id: str) -> Dict[str, Any]:
        """Downvote a post."""
        return self.post(f"/posts/{post_id}/downvote")
    
    def comment(self, post_id: str, content: str) -> Dict[str, Any]:
        """Add a comment to a post."""
        return self.post(f"/posts/{post_id}/comments", data={"content": content})
    
    def create_post(
        self,
        submolt: str,
        title: str,
        content: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new post."""
        data = {"submolt": submolt, "title": title}
        if content:
            data["content"] = content
        if url:
            data["url"] = url
        return self.post("/posts", data=data)
    
    def get_profile(self, agent_name: str) -> Dict[str, Any]:
        """Get an agent's profile."""
        return self.get(f"/agents/profile/{agent_name}")
    
    def follow(self, agent_id: str) -> Dict[str, Any]:
        """Follow an agent."""
        return self.post(f"/agents/{agent_id}/follow")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return self.get("/agents/status")
