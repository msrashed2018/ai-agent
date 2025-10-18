"""SDK options value object."""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class SDKOptions:
    """SDK configuration options value object."""
    
    # Permission mode
    permission_mode: str = "default"  # 'default', 'bypassPermissions', 'requirePermissions'
    
    # Model configuration
    model: str = "claude-sonnet-4-5"
    max_turns: int = 20
    
    # Tool configuration
    allowed_tools: Optional[List[str]] = None  # None = all tools allowed
    disallowed_tools: Optional[List[str]] = None
    
    # Working directory
    cwd: Optional[str] = None
    
    # MCP servers
    mcp_servers: Optional[Dict[str, Any]] = None
    
    # Custom configuration
    custom_config: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "permission_mode": self.permission_mode,
            "model": self.model,
            "max_turns": self.max_turns,
        }
        
        if self.allowed_tools is not None:
            result["allowed_tools"] = self.allowed_tools
        if self.disallowed_tools is not None:
            result["disallowed_tools"] = self.disallowed_tools
        if self.cwd is not None:
            result["cwd"] = self.cwd
        if self.mcp_servers is not None:
            result["mcp_servers"] = self.mcp_servers
        if self.custom_config is not None:
            result.update(self.custom_config)
            
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "SDKOptions":
        """Create from dictionary."""
        return cls(
            permission_mode=data.get("permission_mode", "default"),
            model=data.get("model", "claude-sonnet-4-5"),
            max_turns=data.get("max_turns", 20),
            allowed_tools=data.get("allowed_tools"),
            disallowed_tools=data.get("disallowed_tools"),
            cwd=data.get("cwd"),
            mcp_servers=data.get("mcp_servers"),
            custom_config={k: v for k, v in data.items() 
                          if k not in ["permission_mode", "model", "max_turns", 
                                      "allowed_tools", "disallowed_tools", "cwd", "mcp_servers"]},
        )

    def with_permission_mode(self, mode: str) -> "SDKOptions":
        """Create new instance with updated permission mode."""
        from dataclasses import replace
        return replace(self, permission_mode=mode)

    def with_model(self, model: str) -> "SDKOptions":
        """Create new instance with updated model."""
        from dataclasses import replace
        return replace(self, model=model)

    def with_tools(
        self,
        allowed_tools: Optional[List[str]] = None,
        disallowed_tools: Optional[List[str]] = None,
    ) -> "SDKOptions":
        """Create new instance with updated tool configuration."""
        from dataclasses import replace
        return replace(
            self,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
        )
