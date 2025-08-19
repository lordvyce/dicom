#!/usr/bin/env python3
"""
Simple demo for Enhanced DICOM Viewer v4.0
Demonstrates core functionality without requiring DICOM files
"""
import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_core_functionality():
    """Demonstrate core functionality with synthetic data."""
    print("Demonstrating core functionality...")
    
    # Test ImageProcessor
    from core.image_processor import ImageProcessor
    processor = ImageProcessor()
    print("✓ ImageProcessor created")
    
    # Test window/level processing
    test_image = np.random.rand(256, 256) * 1000 - 500  # Random image data
    processed = processor.apply_window_level(test_image, 0, 1000, 1.0, 0)
    print(f"✓ Window/level processing: {processed.shape}, range {processed.min()}-{processed.max()}")
    
    # Test distance calculation with pixel spacing
    distance = processor.calculate_distance((0, 0), (3, 4), (1.0, 1.0))
    print(f"✓ Distance measurement: {distance:.1f} mm (3-4-5 triangle)")
    
    # Test angle calculation
    angle = processor.calculate_angle((1, 0), (0, 0), (0, 1))
    print(f"✓ Angle measurement: {angle:.1f} degrees (should be 90°)")
    
    # Test HU calculation
    hu_value = processor.get_hounsfield_value(test_image, 128, 128, 1.0, -1024)
    print(f"✓ Hounsfield Unit calculation: {hu_value:.0f} HU")
    
    # Test DicomHandler basic functionality
    from core.dicom_handler import DicomHandler
    handler = DicomHandler()
    print(f"✓ DicomHandler created, initial slice count: {handler.get_slice_count()}")
    
    # Test pixel spacing defaults
    spacing = handler.get_pixel_spacing()
    print(f"✓ Default pixel spacing: {spacing[0]:.1f} x {spacing[1]:.1f} mm")

def demo_measurement_tools():
    """Demonstrate measurement tools."""
    print("\\nDemonstrating measurement tools...")
    
    from core.measurement_tools import MeasurementMode
    print(f"✓ Measurement modes: NONE={MeasurementMode.NONE}, DISTANCE={MeasurementMode.DISTANCE}, ANGLE={MeasurementMode.ANGLE}, CROSSHAIR={MeasurementMode.CROSSHAIR}")
    
    # Test some basic calculations that the measurement tools would use
    from core.image_processor import ImageProcessor
    processor = ImageProcessor()
    
    # Example measurements
    distance_mm = processor.calculate_distance((10, 10), (50, 40), (0.5, 0.5))
    print(f"✓ Example distance measurement: {distance_mm:.1f} mm")
    
    angle_deg = processor.calculate_angle((100, 50), (50, 50), (50, 100))
    print(f"✓ Example angle measurement: {angle_deg:.1f} degrees")

def demo_settings_manager():
    """Demonstrate settings manager."""
    print("\\nDemonstrating settings manager...")
    
    from utils.settings_manager import SettingsManager
    
    # Create a test settings manager
    settings = SettingsManager("demo_viewer")
    print("✓ Settings manager created")
    
    # Test getting default values
    width = settings.get("window.width", 1200)
    height = settings.get("window.height", 800)
    print(f"✓ Default window size: {width} x {height}")
    
    # Test setting values
    settings.set("window.width", 1600)
    new_width = settings.get("window.width")
    print(f"✓ Updated window width: {new_width}")
    
    # Test recent files
    settings.add_recent_file("/demo/test.dcm")
    recent = settings.get_recent_files()
    print(f"✓ Recent files: {len(recent)} entries")

def demo_ui_availability():
    """Check UI component availability."""
    print("\\nChecking UI components...")
    
    try:
        from ui.metadata_browser import MetadataBrowser
        print("✓ MetadataBrowser class available")
        
        from ui.main_window import MainWindow
        print("✓ MainWindow class available")
        
        # Check that key methods exist
        if hasattr(MetadataBrowser, 'update_metadata'):
            print("✓ MetadataBrowser has update_metadata method")
        
        if hasattr(MainWindow, 'setup_ui'):
            print("✓ MainWindow has setup_ui method")
            
        print("✓ All UI components ready (requires PyQt5 and display for actual GUI)")
        
    except Exception as e:
        print(f"✗ UI component issue: {e}")

def main():
    """Run the demo."""
    print("Enhanced DICOM Viewer v4.0 - Core Functionality Demo")
    print("=" * 60)
    
    try:
        demo_core_functionality()
        demo_measurement_tools()
        demo_settings_manager()
        demo_ui_availability()
        
        print("\\n" + "=" * 60)
        print("✓ Core functionality demo completed successfully!")
        print("\\nEnhanced DICOM Viewer v4.0 Features:")
        print("  • Modular architecture with separation of concerns")
        print("  • Advanced measurement tools (distance, angle, crosshair)")
        print("  • Real-world measurements using DICOM pixel spacing")
        print("  • Hounsfield Unit calculations for CT images")
        print("  • Professional metadata browser with search")
        print("  • Comprehensive settings management")
        print("  • Export functionality and keyboard shortcuts")
        print("  • Dark theme optimized for medical imaging")
        
        print("\\nTo run the full GUI application:")
        print("  python main.py")
        print("\\nTo run with a DICOM file:")
        print("  python main.py /path/to/dicom/file.dcm")
        print("\\nTo run with a DICOM folder:")
        print("  python main.py /path/to/dicom/folder/")
        
        print("\\nKey Improvements over v3.0:")
        print("  • Modular codebase (was single file)")
        print("  • Enhanced measurement tools (was basic)")
        print("  • Professional metadata browser (was simple display)")
        print("  • Calibrated real-world measurements (was pixel-based)")
        print("  • Comprehensive settings system (was hardcoded)")
        print("  • Professional UI with dockable panels (was fixed layout)")
        
        return 0
        
    except Exception as e:
        print(f"\\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())