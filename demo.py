#!/usr/bin/env python3
"""
Demo script for Enhanced DICOM Viewer v4.0
Creates synthetic DICOM-like data to demonstrate functionality
"""
import numpy as np
import os
import tempfile
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pydicom
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ExplicitVRLittleEndian
    
    def create_synthetic_dicom(filename, image_data, slice_number=1):
        """Create a synthetic DICOM file with the given image data."""
        
        # Create file meta information
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
        file_meta.MediaStorageSOPInstanceUID = f"1.2.3.{slice_number}"
        file_meta.ImplementationClassUID = "1.2.3.4"
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        
        # Create the main dataset  
        ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\\x00" * 128)
        
        # Patient information
        ds.PatientName = "Demo^Patient"
        ds.PatientID = "DEMO001"
        ds.PatientBirthDate = "19800101"
        ds.PatientSex = "M"
        ds.PatientAge = "044Y"
        
        # Study information
        ds.StudyDate = datetime.now().strftime("%Y%m%d")
        ds.StudyTime = datetime.now().strftime("%H%M%S")
        ds.StudyInstanceUID = "1.2.3.4.5.6.7"
        ds.StudyDescription = "Enhanced DICOM Viewer Demo"
        ds.AccessionNumber = "DEMO123"
        ds.ReferringPhysicianName = "Demo^Doctor"
        
        # Series information
        ds.SeriesDate = ds.StudyDate
        ds.SeriesTime = ds.StudyTime
        ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8"
        ds.SeriesNumber = "1"
        ds.SeriesDescription = "Synthetic Demo Series"
        ds.Modality = "CT"
        
        # Image information
        ds.InstanceNumber = str(slice_number)
        ds.ImagePositionPatient = [0.0, 0.0, float(slice_number * 5)]  # 5mm spacing
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        ds.PixelSpacing = [0.5, 0.5]  # 0.5mm pixel spacing
        ds.SliceThickness = "5.0"
        ds.SliceLocation = float(slice_number * 5)
        
        # Image data
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows, ds.Columns = image_data.shape
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1  # Signed
        
        # Window/Level
        ds.WindowCenter = "40"
        ds.WindowWidth = "400"
        
        # Rescale for HU values
        ds.RescaleIntercept = "-1024"
        ds.RescaleSlope = "1"
        ds.RescaleType = "HU"
        
        # Institution
        ds.InstitutionName = "Demo Medical Center"
        ds.InstitutionAddress = "123 Demo Street, Demo City"
        
        # Set the pixel data
        ds.PixelData = image_data.tobytes()
        
        return ds
    
    def create_demo_series(num_slices=5):
        """Create a series of synthetic DICOM files."""
        temp_dir = tempfile.mkdtemp(prefix="dicom_demo_")
        print(f"Creating demo DICOM series in: {temp_dir}")
        
        files = []
        for i in range(num_slices):
            # Create synthetic image data
            size = 256
            x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
            
            # Create different patterns for each slice
            if i == 0:
                # Circle
                image = np.where(x**2 + y**2 < 0.5, 200, -800)
            elif i == 1:
                # Square
                image = np.where((np.abs(x) < 0.5) & (np.abs(y) < 0.5), 100, -900)
            elif i == 2:
                # Cross pattern
                image = np.where((np.abs(x) < 0.1) | (np.abs(y) < 0.1), 300, -700)
            elif i == 3:
                # Gradient
                image = (x + y) * 500 - 200
            else:
                # Random noise pattern
                image = np.random.normal(-400, 200, (size, size))
            
            # Add some noise and convert to float first
            image = image.astype(np.float64)
            image += np.random.normal(0, 10, image.shape)
            
            # Convert to 16-bit signed integer
            image = image.astype(np.int16)
            
            # Create DICOM file
            filename = os.path.join(temp_dir, f"slice_{i+1:03d}.dcm")
            ds = create_synthetic_dicom(filename, image, i+1)
            ds.save_as(filename)
            files.append(filename)
            
            print(f"  Created slice {i+1}/{num_slices}: {os.path.basename(filename)}")
        
        return temp_dir, files
    
    def demo_core_functionality():
        """Demonstrate core functionality with synthetic data."""
        print("\\nDemonstrating core functionality...")
        
        # Create demo series
        demo_dir, demo_files = create_demo_series(3)
        
        # Test DicomHandler
        from core.dicom_handler import DicomHandler
        handler = DicomHandler()
        
        print(f"Loading {len(demo_files)} demo DICOM files...")
        success = handler.load_dicom_series(demo_files)
        
        if success:
            print(f"✓ Successfully loaded {handler.get_slice_count()} slices")
            
            # Test pixel spacing
            spacing = handler.get_pixel_spacing()
            print(f"✓ Pixel spacing: {spacing[0]:.1f} x {spacing[1]:.1f} mm")
            
            # Test window/level defaults
            level, width = handler.get_window_level_defaults()
            print(f"✓ Default W/L: {level:.0f}/{width:.0f}")
            
            # Test image data
            pixel_data = handler.get_pixel_data()
            if pixel_data is not None:
                print(f"✓ Image data: {pixel_data.shape}, range {pixel_data.min():.0f} to {pixel_data.max():.0f}")
            
            # Test ImageProcessor
            from core.image_processor import ImageProcessor
            processor = ImageProcessor()
            
            # Process image
            processed = processor.apply_window_level(pixel_data, level, width, 1.0, -1024)
            print(f"✓ Processed image: {processed.shape}, range {processed.min()} to {processed.max()}")
            
            # Test measurements
            distance = processor.calculate_distance((0, 0), (100, 100), spacing)
            print(f"✓ Distance measurement: {distance:.1f} mm")
            
            angle = processor.calculate_angle((100, 0), (0, 0), (0, 100))
            print(f"✓ Angle measurement: {angle:.1f} degrees")
            
            # Test HU calculation
            hu_value = processor.get_hounsfield_value(pixel_data, 128, 128, 1.0, -1024)
            print(f"✓ HU value at center: {hu_value:.0f} HU")
            
        else:
            print("✗ Failed to load demo DICOM files")
            return None, None
        
        return demo_dir, handler
    
    def demo_ui_creation():
        """Demonstrate UI creation (without showing)."""
        print("\\nDemonstrating UI components...")
        
        try:
            # Test settings manager
            from utils.settings_manager import SettingsManager
            settings = SettingsManager("demo_app")
            print(f"✓ Settings manager: {settings.get('window.width')} x {settings.get('window.height')}")
            
            # Test metadata browser (class only)
            from ui.metadata_browser import MetadataBrowser
            print("✓ Metadata browser class available")
            
            # Test main window (class only) 
            from ui.main_window import MainWindow
            print("✓ Main window class available")
            
            print("✓ All UI components available (GUI display requires X11)")
            
        except Exception as e:
            print(f"✗ UI component error: {e}")
    
    def main():
        """Run the demo."""
        print("Enhanced DICOM Viewer v4.0 - Interactive Demo")
        print("=" * 50)
        
        # Test if we can create synthetic DICOMs
        demo_dir, handler = demo_core_functionality()
        
        if demo_dir and handler:
            # Demo UI components
            demo_ui_creation()
            
            print("\\n" + "=" * 50)
            print("✓ Demo completed successfully!")
            print(f"\\nDemo DICOM files created in: {demo_dir}")
            print("\\nTo run the enhanced viewer with demo data:")
            print(f"  python main.py {demo_dir}")
            print("\\nFeatures to try:")
            print("  - Navigate slices with arrow keys")
            print("  - Use crosshair mode to see pixel values")
            print("  - Measure distances and angles")
            print("  - Browse comprehensive metadata")
            print("  - Export images with annotations")
            
        else:
            print("\\n✗ Demo failed - check dependencies")
            return 1
        
        return 0

except ImportError as e:
    def main():
        print("Enhanced DICOM Viewer v4.0 - Demo")
        print("=" * 50)
        print(f"✗ Missing dependencies: {e}")
        print("\\nTo install required packages:")
        print("  pip install PyQt5 pydicom numpy pylibjpeg pylibjpeg-libjpeg")
        print("\\nThen run: python demo.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())