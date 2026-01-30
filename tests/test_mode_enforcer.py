"""
Mode Enforcer Tests
TDD tests for permission level enforcement
"""

def test_lurk_mode_allows_read():
    """Given mode=lurk and read action, should allow"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="lurk")
    
    read_actions = [
        Action.READ_FEED,
        Action.READ_POST,
        Action.READ_COMMENTS,
        Action.READ_PROFILE,
        Action.READ_SUBMOLT,
    ]
    
    for action in read_actions:
        result = enforcer.check(action)
        assert result.allowed, f"Lurk mode should allow {action}"
        assert not result.requires_approval


def test_lurk_mode_blocks_write():
    """Given mode=lurk and write action, should block"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="lurk")
    
    write_actions = [
        Action.UPVOTE,
        Action.DOWNVOTE,
        Action.COMMENT,
        Action.POST,
        Action.FOLLOW,
    ]
    
    for action in write_actions:
        result = enforcer.check(action)
        assert not result.allowed, f"Lurk mode should block {action}"


def test_engage_mode_allows_upvote():
    """Given mode=engage and upvote action, should allow"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="engage")
    
    result = enforcer.check(Action.UPVOTE)
    assert result.allowed
    assert not result.requires_approval


def test_engage_mode_requires_approval_for_comment():
    """Given mode=engage and comment action, should require approval"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="engage")
    
    result = enforcer.check(Action.COMMENT)
    assert result.allowed
    assert result.requires_approval


def test_engage_mode_requires_approval_for_post():
    """Given mode=engage and post action, should require approval"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="engage")
    
    result = enforcer.check(Action.POST)
    assert result.allowed
    assert result.requires_approval


def test_active_mode_allows_comment():
    """Given mode=active and comment action, should allow without approval"""
    from mode_enforcer import ModeEnforcer, Action
    
    enforcer = ModeEnforcer(mode="active")
    
    result = enforcer.check(Action.COMMENT)
    assert result.allowed
    assert not result.requires_approval


def test_any_mode_requires_approval_for_post():
    """Given any mode and post action, should require approval"""
    from mode_enforcer import ModeEnforcer, Action
    
    for mode in ["lurk", "engage", "active"]:
        enforcer = ModeEnforcer(mode=mode)
        result = enforcer.check(Action.POST)
        
        if mode == "lurk":
            assert not result.allowed, "Lurk should block posts"
        else:
            assert result.requires_approval, f"{mode} mode should require approval for posts"


def test_mode_hierarchy():
    """Mode permissions should follow lurk < engage < active hierarchy"""
    from mode_enforcer import ModeEnforcer, Action
    
    # engage should include lurk permissions
    engage = ModeEnforcer(mode="engage")
    assert engage.check(Action.READ_FEED).allowed
    
    # active should include engage permissions
    active = ModeEnforcer(mode="active")
    assert active.check(Action.READ_FEED).allowed
    assert active.check(Action.UPVOTE).allowed


if __name__ == "__main__":
    tests = [
        test_lurk_mode_allows_read,
        test_lurk_mode_blocks_write,
        test_engage_mode_allows_upvote,
        test_engage_mode_requires_approval_for_comment,
        test_engage_mode_requires_approval_for_post,
        test_active_mode_allows_comment,
        test_any_mode_requires_approval_for_post,
        test_mode_hierarchy,
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
