"""
Configuration management for HMAS Bridge Layer.

Supports configuration via:
- YAML config file (tools/config.yaml)
- Environment variables (HMAS_* prefix)
"""

import os
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Config:
    """Configuration manager for Bridge Layer tools."""

    # Default configuration values
    DEFAULTS = {
        "lead_dev": {
            "interface": "gemini-cli",
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 5,
        },
        "context": {
            "max_tokens": 8000,
            "include_architecture": True,
            "include_roadmap": False,
            "truncation_strategy": "recent_first",
        },
        "output": {
            "default_format": "text",
            "include_timestamps": True,
            "log_queries": True,
            "log_file": "tools/logs/bridge.log",
        },
        "project": {
            "docs_path": "docs/",
            "milestones_path": "docs/01_milestones/",
            "architecture_file": "docs/00_global/ARCHITECTURE.md",
            "roadmap_file": "docs/00_global/ROADMAP.md",
            "workflow_file": "docs/00_global/WORKFLOW.md",
        },
    }

    # Environment variable mappings
    ENV_MAPPINGS = {
        "HMAS_LEAD_INTERFACE": ("lead_dev", "interface"),
        "HMAS_CONTEXT_MAX_TOKENS": ("context", "max_tokens"),
        "HMAS_LOG_LEVEL": ("output", "log_level"),
        "HMAS_CONFIG_PATH": None,  # Special handling
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file. If None, uses default location
                        or HMAS_CONFIG_PATH environment variable.
        """
        self._config: dict[str, Any] = {}
        self._project_root = self._find_project_root()

        # Load configuration in order of precedence (later overrides earlier)
        self._load_defaults()
        self._load_yaml_config(config_path)
        self._load_env_variables()

    def _find_project_root(self) -> Path:
        """Find the project root directory (containing tools/)."""
        current = Path(__file__).resolve()
        # Navigate up from tools/lib/config.py to project root
        return current.parent.parent.parent

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = self._deep_copy(self.DEFAULTS)

    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a configuration dict."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj

    def _load_yaml_config(self, config_path: Optional[str]) -> None:
        """Load configuration from YAML file if available."""
        if not YAML_AVAILABLE:
            return

        # Determine config path
        if config_path is None:
            config_path = os.environ.get("HMAS_CONFIG_PATH")

        if config_path is None:
            config_path = self._project_root / "tools" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            return

        try:
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)

            if yaml_config and isinstance(yaml_config, dict):
                # Get the 'bridge' section if it exists
                bridge_config = yaml_config.get("bridge", {})
                if bridge_config:
                    self._merge_config(bridge_config)

                # Get the 'project' section if it exists
                project_config = yaml_config.get("project", {})
                if project_config:
                    self._merge_config({"project": project_config})
        except Exception:
            # Silently ignore config file errors, use defaults
            pass

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration into existing config."""
        for key, value in new_config.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._config[key].update(value)
            else:
                self._config[key] = value

    def _load_env_variables(self) -> None:
        """Load configuration from environment variables."""
        for env_var, path in self.ENV_MAPPINGS.items():
            if path is None:
                continue

            value = os.environ.get(env_var)
            if value is not None:
                section, key = path
                # Convert value to appropriate type
                if key == "max_tokens":
                    value = int(value)
                self._config[section][key] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value by key path.

        Args:
            *keys: Key path (e.g., "lead_dev", "timeout")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def docs_path(self) -> Path:
        """Get the documentation directory path."""
        return self._project_root / self.get("project", "docs_path", default="docs/")

    @property
    def milestones_path(self) -> Path:
        """Get the milestones directory path."""
        return self._project_root / self.get("project", "milestones_path", default="docs/01_milestones/")

    @property
    def architecture_file(self) -> Path:
        """Get the architecture file path."""
        return self._project_root / self.get("project", "architecture_file", default="docs/00_global/ARCHITECTURE.md")

    @property
    def roadmap_file(self) -> Path:
        """Get the roadmap file path."""
        return self._project_root / self.get("project", "roadmap_file", default="docs/00_global/ROADMAP.md")

    @property
    def workflow_file(self) -> Path:
        """Get the workflow file path."""
        return self._project_root / self.get("project", "workflow_file", default="docs/00_global/WORKFLOW.md")

    @property
    def max_context_tokens(self) -> int:
        """Get the maximum context size in tokens."""
        return self.get("context", "max_tokens", default=8000)

    @property
    def default_format(self) -> str:
        """Get the default output format."""
        return self.get("output", "default_format", default="text")
