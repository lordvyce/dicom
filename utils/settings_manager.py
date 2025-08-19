"""
Settings Manager - Handle application settings and preferences
"""
import os
import json
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages application settings and preferences."""
    
    def __init__(self, app_name: str = "enhanced_dicom_viewer"):
        self.app_name = app_name
        self.settings_dir = self._get_settings_directory()
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.default_settings = self._get_default_settings()
        self._ensure_settings_directory()
        self.settings = self._load_settings()
    
    def _get_settings_directory(self) -> str:
        """Get the settings directory path."""
        if os.name == 'nt':  # Windows
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        else:  # Unix-like
            base_dir = os.path.expanduser('~/.config')
        
        return os.path.join(base_dir, self.app_name)
    
    def _ensure_settings_directory(self):
        """Ensure the settings directory exists."""
        os.makedirs(self.settings_dir, exist_ok=True)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            "window": {
                "width": 1400,
                "height": 1000,
                "maximized": False,
                "splitter_sizes": [300, 600, 400]
            },
            "display": {
                "default_preset": "Soft Tissue",
                "auto_fit": True,
                "interpolation": True
            },
            "measurements": {
                "default_mode": "crosshair",
                "show_pixel_values": True,
                "show_hu_values": True,
                "line_thickness": 2
            },
            "export": {
                "default_format": "PNG",
                "default_quality": 95,
                "include_annotations": True
            },
            "ui": {
                "theme": "dark",
                "font_size": 9,
                "show_toolbar": True,
                "show_statusbar": True
            },
            "recent_files": [],
            "max_recent_files": 10
        }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r') as f:
                loaded_settings = json.load(f)
            
            # Merge with defaults to handle missing keys
            settings = self.default_settings.copy()
            self._merge_dict(settings, loaded_settings)
            return settings
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def _merge_dict(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Recursively merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dict(target[key], value)
            else:
                target[key] = value
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to setting (e.g., "window.width")
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set a setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to setting (e.g., "window.width")
            value: Value to set
        """
        keys = key_path.split('.')
        target = self.settings
        
        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the final value
        target[keys[-1]] = value
    
    def add_recent_file(self, file_path: str):
        """Add a file to recent files list."""
        recent_files = self.get("recent_files", [])
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Limit list size
        max_files = self.get("max_recent_files", 10)
        recent_files = recent_files[:max_files]
        
        self.set("recent_files", recent_files)
    
    def get_recent_files(self) -> list:
        """Get list of recent files."""
        return self.get("recent_files", [])
    
    def clear_recent_files(self):
        """Clear recent files list."""
        self.set("recent_files", [])
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.default_settings.copy()
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file."""
        try:
            with open(file_path, 'r') as f:
                imported_settings = json.load(f)
            
            # Merge with current settings
            self._merge_dict(self.settings, imported_settings)
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing settings: {e}")
            return False