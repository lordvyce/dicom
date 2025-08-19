#!/usr/bin/env python3
"""
Test script to validate enhanced DICOM viewer functionality
"""
import sys
import os
import tempfile
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_modules():
    """Test core module functionality."""
    print("Testing core modules...")
    
    # Test DicomHandler
    from core.dicom_handler import DicomHandler
    handler = DicomHandler()
    assert handler.get_slice_count() == 0
    print("✓ DicomHandler initialized")
    
    # Test ImageProcessor
    from core.image_processor import ImageProcessor
    processor = ImageProcessor()
    
    # Test window/level processing
    test_image = np.random.rand(100, 100) * 1000
    processed = processor.apply_window_level(test_image, 500, 1000)
    assert processed.shape == test_image.shape
    assert processed.dtype == np.uint8
    print("✓ Window/level processing works")
    
    # Test distance calculation
    distance = processor.calculate_distance((0, 0), (3, 4), (1.0, 1.0))
    assert abs(distance - 5.0) < 0.01  # 3-4-5 triangle
    print("✓ Distance calculation works")
    
    # Test angle calculation
    angle = processor.calculate_angle((1, 0), (0, 0), (0, 1))
    assert abs(angle - 90.0) < 0.01  # 90 degree angle
    print("✓ Angle calculation works")
    
    # Test HU value calculation
    hu_value = processor.get_hounsfield_value(test_image, 50, 50, 1.0, -1024)
    assert hu_value is not None
    print("✓ Hounsfield Unit calculation works")

def test_settings_manager():
    """Test settings manager functionality."""
    print("\\nTesting settings manager...")
    
    from utils.settings_manager import SettingsManager
    
    # Create temporary settings manager
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the settings directory
        original_method = SettingsManager._get_settings_directory
        SettingsManager._get_settings_directory = lambda self: temp_dir
        
        settings = SettingsManager("test_app")
        
        # Test default settings
        assert settings.get("window.width") == 1400
        print("✓ Default settings loaded")
        
        # Test setting values
        settings.set("window.width", 1600)
        assert settings.get("window.width") == 1600
        print("✓ Setting values works")
        
        # Test saving/loading
        assert settings.save_settings()
        print("✓ Settings save works")
        
        # Test recent files
        settings.add_recent_file("/test/file.dcm")
        recent = settings.get_recent_files()
        assert len(recent) == 1
        assert recent[0] == "/test/file.dcm"
        print("✓ Recent files works")
        
        # Restore original method
        SettingsManager._get_settings_directory = original_method

def test_measurement_tools():
    """Test measurement tools without GUI."""
    print("\\nTesting measurement tools...")
    
    from core.measurement_tools import MeasurementMode
    from PyQt5.QtCore import QPointF
    
    # Test measurement modes
    assert MeasurementMode.NONE == 0
    assert MeasurementMode.DISTANCE == 1
    assert MeasurementMode.ANGLE == 2
    assert MeasurementMode.CROSSHAIR == 3
    print("✓ Measurement modes defined")

def test_module_imports():
    """Test that all modules can be imported."""
    print("\\nTesting module imports...")
    
    modules_to_test = [
        "core.dicom_handler",
        "core.image_processor", 
        "core.measurement_tools",
        "utils.settings_manager"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {module_name}: {e}")
            return False
    
    return True

def test_ui_modules():
    """Test UI modules (without actually creating GUI)."""
    print("\\nTesting UI modules...")
    
    try:
        # Test that UI modules can be imported
        from ui.metadata_browser import MetadataBrowser
        from ui.main_window import MainWindow
        print("✓ UI modules can be imported")
        
        # Note: We can't actually instantiate these without a QApplication
        # but we can verify the classes exist
        assert hasattr(MetadataBrowser, 'update_metadata')
        assert hasattr(MainWindow, 'setup_ui')
        print("✓ UI classes have expected methods")
        
    except ImportError as e:
        print(f"✗ UI import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Enhanced DICOM Viewer v4.0 - Test Suite")
    print("=" * 50)
    
    try:
        if not test_module_imports():
            return 1
        
        test_core_modules()
        test_settings_manager()
        test_measurement_tools()
        
        if not test_ui_modules():
            return 1
        
        print("\\n" + "=" * 50)
        print("✓ All tests passed! Enhanced DICOM Viewer is ready.")
        print("\\nTo run the application:")
        print("  python main.py")
        print("\\nTo run with a DICOM file:")
        print("  python main.py /path/to/file.dcm")
        
        return 0
        
    except Exception as e:
        print(f"\\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())