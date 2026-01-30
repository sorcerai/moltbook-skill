"""
Engagement Manager
Handles safe engagement with moltbook with human approval workflow.
All high-impact actions require explicit approval before execution.
"""
from dataclasses import dataclass
from typing import Optional, Any, Dict

from mode_enforcer import ModeEnforcer, Action


@dataclass
class ActionResult:
    """Result of an engagement action."""
    success: bool
    reason: str = ""
    data: Optional[Dict[str, Any]] = None


@dataclass
class DraftAction:
    """A drafted action pending human approval."""
    action_type: str  # "comment", "post", "follow"
    target_id: str  # post_id or agent_id
    draft_content: str
    requires_approval: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def to_display(self) -> str:
        """Format for human review."""
        return (
            f"**Pending {self.action_type.upper()}**\n"
            f"Target: {self.target_id}\n"
            f"Content:\n{self.draft_content}\n\n"
            f"Reply 'approve' to send, 'reject' to cancel."
        )


class EngagementManager:
    """Manages moltbook engagement with permission enforcement."""
    
    def __init__(self, client, enforcer: ModeEnforcer):
        """
        Initialize engagement manager.
        
        Args:
            client: MoltbookClient for API calls
            enforcer: ModeEnforcer for permission checks
        """
        self.client = client
        self.enforcer = enforcer
        self._pending_drafts: Dict[str, DraftAction] = {}
    
    # === Low-impact actions (no approval needed in engage+) ===
    
    def upvote(self, post_id: str) -> ActionResult:
        """
        Upvote a post.
        
        Args:
            post_id: Post to upvote
            
        Returns:
            ActionResult
        """
        perm = self.enforcer.check(Action.UPVOTE)
        if not perm.allowed:
            return ActionResult(
                success=False,
                reason=f"Blocked: {perm.reason}"
            )
        
        try:
            result = self.client.upvote(post_id)
            return ActionResult(success=True, data=result)
        except Exception as e:
            return ActionResult(success=False, reason=str(e))
    
    def downvote(self, post_id: str) -> ActionResult:
        """Downvote a post."""
        perm = self.enforcer.check(Action.DOWNVOTE)
        if not perm.allowed:
            return ActionResult(
                success=False,
                reason=f"Blocked: {perm.reason}"
            )
        
        try:
            result = self.client.downvote(post_id)
            return ActionResult(success=True, data=result)
        except Exception as e:
            return ActionResult(success=False, reason=str(e))
    
    # === High-impact actions (require approval) ===
    
    def draft_comment(self, post_id: str, content: str) -> DraftAction:
        """
        Draft a comment for human approval.
        
        Args:
            post_id: Post to comment on
            content: Comment content
            
        Returns:
            DraftAction pending approval
        """
        perm = self.enforcer.check(Action.COMMENT)
        
        draft = DraftAction(
            action_type="comment",
            target_id=post_id,
            draft_content=content,
            requires_approval=perm.requires_approval,
            metadata={"post_id": post_id}
        )
        
        # Store for later execution
        draft_key = f"comment_{post_id}"
        self._pending_drafts[draft_key] = draft
        
        return draft
    
    def draft_post(
        self,
        submolt: str,
        title: str,
        content: Optional[str] = None,
        url: Optional[str] = None
    ) -> DraftAction:
        """
        Draft a post for human approval.
        
        Args:
            submolt: Target submolt
            title: Post title
            content: Post content (optional)
            url: Link URL (optional)
            
        Returns:
            DraftAction pending approval
        """
        display_content = content or url or "(no content)"
        
        draft = DraftAction(
            action_type="post",
            target_id=submolt,
            draft_content=display_content,
            requires_approval=True,  # Posts ALWAYS require approval
            metadata={
                "submolt": submolt,
                "title": title,
                "content": content,
                "url": url
            }
        )
        
        draft_key = f"post_{submolt}_{title[:20]}"
        self._pending_drafts[draft_key] = draft
        
        return draft
    
    def execute_with_approval(
        self,
        draft: DraftAction,
        approved: bool
    ) -> ActionResult:
        """
        Execute a drafted action after human approval.
        
        Args:
            draft: The DraftAction to execute
            approved: Whether human approved
            
        Returns:
            ActionResult
        """
        if not approved:
            return ActionResult(
                success=False,
                reason="Action rejected by human"
            )
        
        try:
            if draft.action_type == "comment":
                result = self.client.comment(
                    draft.metadata["post_id"],
                    draft.draft_content
                )
                return ActionResult(success=True, data=result)
            
            elif draft.action_type == "post":
                result = self.client.create_post(
                    submolt=draft.metadata["submolt"],
                    title=draft.metadata["title"],
                    content=draft.metadata.get("content"),
                    url=draft.metadata.get("url")
                )
                return ActionResult(success=True, data=result)
            
            else:
                return ActionResult(
                    success=False,
                    reason=f"Unknown action type: {draft.action_type}"
                )
                
        except Exception as e:
            return ActionResult(success=False, reason=str(e))
    
    # === Direct actions (for active mode) ===
    
    def comment_direct(self, post_id: str, content: str) -> ActionResult:
        """
        Comment directly without approval flow (for active mode).
        
        Args:
            post_id: Post to comment on
            content: Comment content
            
        Returns:
            ActionResult
        """
        perm = self.enforcer.check(Action.COMMENT)
        if not perm.allowed:
            return ActionResult(
                success=False,
                reason=f"Blocked: {perm.reason}"
            )
        
        # In active mode, can skip approval
        if perm.requires_approval:
            return ActionResult(
                success=False,
                reason="Comment requires approval in this mode. Use draft_comment instead."
            )
        
        try:
            result = self.client.comment(post_id, content)
            return ActionResult(success=True, data=result)
        except Exception as e:
            return ActionResult(success=False, reason=str(e))
