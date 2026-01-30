"""
Engagement Actions Tests
TDD tests for safe engagement with human approval workflow
"""
from unittest.mock import Mock, patch


def test_upvote_in_engage_mode_calls_api():
    """Given upvote request in engage+ mode, should call POST /posts/{id}/upvote"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    mock_client.upvote.return_value = {"success": True}
    
    enforcer = ModeEnforcer(mode="engage")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    result = manager.upvote("post_123")
    
    assert result.success
    mock_client.upvote.assert_called_once_with("post_123")


def test_upvote_in_lurk_mode_blocked():
    """Given upvote request in lurk mode, should block"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    enforcer = ModeEnforcer(mode="lurk")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    result = manager.upvote("post_123")
    
    assert not result.success
    assert "lurk" in result.reason.lower() or "blocked" in result.reason.lower()
    mock_client.upvote.assert_not_called()


def test_comment_returns_draft_for_approval():
    """Given comment request, should draft and present to human first"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    enforcer = ModeEnforcer(mode="engage")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    result = manager.draft_comment("post_123", "Great discussion!")
    
    assert result.requires_approval
    assert result.draft_content == "Great discussion!"
    assert result.action_type == "comment"
    mock_client.comment.assert_not_called()  # Should NOT call API yet


def test_comment_with_approval_calls_api():
    """Given human approval for comment, should call POST /posts/{id}/comments"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    mock_client.comment.return_value = {"success": True, "comment": {"id": "c1"}}
    
    enforcer = ModeEnforcer(mode="engage")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    # Draft first
    draft = manager.draft_comment("post_123", "Great discussion!")
    
    # Then approve
    result = manager.execute_with_approval(draft, approved=True)
    
    assert result.success
    mock_client.comment.assert_called_once_with("post_123", "Great discussion!")


def test_post_returns_draft_for_approval():
    """Given post request, should draft and present to human first"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    enforcer = ModeEnforcer(mode="active")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    result = manager.draft_post(
        submolt="clawdbot",
        title="New Skill Announcement",
        content="I just shipped a secure moltbook skill!"
    )
    
    assert result.requires_approval
    assert result.action_type == "post"
    assert result.draft_content == "I just shipped a secure moltbook skill!"
    mock_client.create_post.assert_not_called()


def test_post_with_approval_calls_api():
    """Given human approval for post, should call POST /posts"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    mock_client.create_post.return_value = {"success": True, "post": {"id": "p1"}}
    
    enforcer = ModeEnforcer(mode="active")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    # Draft first
    draft = manager.draft_post(
        submolt="clawdbot",
        title="Test",
        content="Content"
    )
    
    # Then approve
    result = manager.execute_with_approval(draft, approved=True)
    
    assert result.success
    mock_client.create_post.assert_called_once()


def test_rejected_draft_not_sent():
    """Given rejected draft, should not call API"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    enforcer = ModeEnforcer(mode="engage")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    draft = manager.draft_comment("post_123", "Bad comment")
    result = manager.execute_with_approval(draft, approved=False)
    
    assert not result.success
    assert "rejected" in result.reason.lower() or "denied" in result.reason.lower()
    mock_client.comment.assert_not_called()


def test_active_mode_comment_no_approval_needed():
    """Given mode=active and comment action, can skip approval flow"""
    from engagement import EngagementManager
    from mode_enforcer import ModeEnforcer
    
    mock_client = Mock()
    mock_client.comment.return_value = {"success": True, "comment": {"id": "c1"}}
    
    enforcer = ModeEnforcer(mode="active")
    manager = EngagementManager(client=mock_client, enforcer=enforcer)
    
    # Direct comment without draft flow
    result = manager.comment_direct("post_123", "Quick response")
    
    assert result.success
    mock_client.comment.assert_called_once()


if __name__ == "__main__":
    tests = [
        test_upvote_in_engage_mode_calls_api,
        test_upvote_in_lurk_mode_blocked,
        test_comment_returns_draft_for_approval,
        test_comment_with_approval_calls_api,
        test_post_returns_draft_for_approval,
        test_post_with_approval_calls_api,
        test_rejected_draft_not_sent,
        test_active_mode_comment_no_approval_needed,
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
