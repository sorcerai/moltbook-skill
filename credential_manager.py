"""
Credential Manager
Isolated credential storage for moltbook skill.
Credentials stored in ~/.config/moltbook/credentials.json - NEVER in memory files.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "moltbook"


class CredentialManager:
    """Manages moltbook credentials in isolated storage."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        self.credentials_path = self.config_dir / "credentials.json"
    
    def store(
        self,
        api_key: str,
        agent_id: str,
        mode: str = "lurk",
        claimed: bool = False,
        **extra
    ) -> None:
        """
        Store credentials in isolated config file.
        
        Args:
            api_key: Moltbook API key (NEVER log this)
            agent_id: Agent UUID
            mode: Permission mode (lurk|engage|active)
            claimed: Whether agent has been claimed
            **extra: Additional fields to store
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "api_key": api_key,
            "agent_id": agent_id,
            "mode": mode,
            "claimed": claimed,
            **extra
        }
        
        self.credentials_path.write_text(json.dumps(data, indent=2))
    
    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load credentials from isolated config file.
        
        Returns:
            Credentials dict or None if not found
        """
        if not self.credentials_path.exists():
            return None
        
        try:
            return json.loads(self.credentials_path.read_text())
        except (json.JSONDecodeError, IOError):
            return None
    
    def set_mode(self, mode: str) -> None:
        """
        Update permission mode.
        
        Args:
            mode: New mode (lurk|engage|active)
        """
        if mode not in ("lurk", "engage", "active"):
            raise ValueError(f"Invalid mode: {mode}. Must be lurk|engage|active")
        
        creds = self.load()
        if creds is None:
            raise RuntimeError("No credentials found. Store credentials first.")
        
        creds["mode"] = mode
        self.credentials_path.write_text(json.dumps(creds, indent=2))
    
    def get_api_key(self) -> Optional[str]:
        """Get API key for authenticated requests."""
        creds = self.load()
        return creds.get("api_key") if creds else None
    
    def get_mode(self) -> str:
        """Get current permission mode. Defaults to lurk."""
        creds = self.load()
        return creds.get("mode", "lurk") if creds else "lurk"
    
    def get_safe_summary(self) -> str:
        """
        Get a summary safe for memory files.
        API key is NEVER included.
        
        Returns:
            Safe summary string for logging
        """
        creds = self.load()
        if creds is None:
            return "No moltbook credentials configured."
        
        return (
            f"Moltbook Agent: {creds.get('agent_id', 'unknown')}\n"
            f"Mode: {creds.get('mode', 'lurk')}\n"
            f"Claimed: {creds.get('claimed', False)}\n"
            f"API Key: [REDACTED]"
        )
    
    def is_claimed(self) -> bool:
        """Check if agent has been claimed."""
        creds = self.load()
        return creds.get("claimed", False) if creds else False
    
    def set_claimed(self, claimed: bool = True) -> None:
        """Update claimed status."""
        creds = self.load()
        if creds is None:
            raise RuntimeError("No credentials found.")
        
        creds["claimed"] = claimed
        self.credentials_path.write_text(json.dumps(creds, indent=2))
