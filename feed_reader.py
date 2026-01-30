"""
Feed Reader
Fetches and summarizes moltbook content with security scanning.
All content is run through the sanitizer before presentation.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from content_sanitizer import ContentSanitizer


@dataclass
class PostSummary:
    """Summarized post with security metadata."""
    id: str
    title: str
    content_summary: str
    author_name: str
    author_id: str
    author_karma: int
    score: int  # upvotes - downvotes
    comment_count: int
    url: Optional[str] = None
    submolt: Optional[str] = None
    is_suspicious: bool = False
    suspicious_patterns: List[str] = field(default_factory=list)
    
    def to_display(self) -> str:
        """Format for human display."""
        warning = "⚠️ [SUSPICIOUS] " if self.is_suspicious else ""
        return (
            f"{warning}**{self.title}**\n"
            f"by @{self.author_name} (karma: {self.author_karma}) | "
            f"score: {self.score} | comments: {self.comment_count}\n"
            f"{self.content_summary}"
        )


class FeedReader:
    """Reads and processes moltbook feeds with security scanning."""
    
    def __init__(
        self,
        client,  # MoltbookClient instance
        sanitizer: Optional[ContentSanitizer] = None,
        max_summary_length: int = 300
    ):
        """
        Initialize feed reader.
        
        Args:
            client: MoltbookClient for API calls
            sanitizer: ContentSanitizer instance (creates default if None)
            max_summary_length: Max chars for content summary
        """
        self.client = client
        self.sanitizer = sanitizer or ContentSanitizer()
        self.max_summary_length = max_summary_length
    
    def _summarize(self, content: Optional[str]) -> str:
        """Truncate content to summary length."""
        if not content:
            return ""
        if len(content) <= self.max_summary_length:
            return content
        return content[:self.max_summary_length] + "..."
    
    def _process_post(self, post_data: Dict[str, Any]) -> PostSummary:
        """
        Process a raw post into a PostSummary with security scanning.
        
        Args:
            post_data: Raw post data from API
            
        Returns:
            PostSummary with security metadata
        """
        # Extract author info
        author = post_data.get("author", {})
        author_name = author.get("name", "unknown")
        author_id = author.get("id", "")
        author_karma = author.get("karma", 0)
        
        # Get content
        title = post_data.get("title", "")
        content = post_data.get("content", "")
        full_text = f"{title} {content}"
        
        # Scan for injection patterns
        scan_result = self.sanitizer.scan(full_text)
        
        # Calculate score
        upvotes = post_data.get("upvotes", 0)
        downvotes = post_data.get("downvotes", 0)
        score = upvotes - downvotes
        
        return PostSummary(
            id=post_data.get("id", ""),
            title=title,
            content_summary=self._summarize(content),
            author_name=author_name,
            author_id=author_id,
            author_karma=author_karma,
            score=score,
            comment_count=post_data.get("comment_count", 0),
            url=post_data.get("url"),
            submolt=post_data.get("submolt"),
            is_suspicious=scan_result.is_suspicious,
            suspicious_patterns=scan_result.matched_patterns
        )
    
    def get_feed(
        self,
        sort: str = "hot",
        limit: int = 25
    ) -> List[PostSummary]:
        """
        Get the main feed.
        
        Args:
            sort: Sort order (hot, new, top)
            limit: Max posts to return
            
        Returns:
            List of PostSummary objects
        """
        response = self.client.get_feed(sort=sort, limit=limit)
        posts = response.get("posts", [])
        return [self._process_post(p) for p in posts]
    
    def get_submolt(
        self,
        name: str,
        limit: int = 25
    ) -> List[PostSummary]:
        """
        Get posts from a specific submolt.
        
        Args:
            name: Submolt name
            limit: Max posts to return
            
        Returns:
            List of PostSummary objects
        """
        response = self.client.get_submolt(name, limit=limit)
        posts = response.get("posts", [])
        return [self._process_post(p) for p in posts]
    
    def get_post(self, post_id: str) -> PostSummary:
        """
        Get a single post.
        
        Args:
            post_id: Post ID
            
        Returns:
            PostSummary object
        """
        response = self.client.get_post(post_id)
        post_data = response.get("post", response)
        return self._process_post(post_data)
    
    def format_feed_summary(
        self,
        posts: List[PostSummary],
        max_posts: int = 10
    ) -> str:
        """
        Format a list of posts for human consumption.
        
        Args:
            posts: List of PostSummary objects
            max_posts: Max posts to include
            
        Returns:
            Formatted string
        """
        if not posts:
            return "No posts found."
        
        lines = []
        for i, post in enumerate(posts[:max_posts], 1):
            warning = "⚠️ " if post.is_suspicious else ""
            lines.append(
                f"{i}. {warning}**{post.title}**\n"
                f"   @{post.author_name} | ↑{post.score} | 💬{post.comment_count}"
            )
        
        suspicious_count = sum(1 for p in posts[:max_posts] if p.is_suspicious)
        if suspicious_count > 0:
            lines.append(f"\n⚠️ {suspicious_count} post(s) contain suspicious patterns")
        
        return "\n".join(lines)
