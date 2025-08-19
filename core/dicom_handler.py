"""
DICOM Handler - Core functionality for loading and processing DICOM files
"""
import os
import pydicom
import numpy as np
from typing import List, Optional, Tuple


class DicomHandler:
    """Handles DICOM file loading, sorting, and basic processing."""
    
    def __init__(self):
        self.slices: List[pydicom.Dataset] = []
        self.current_slice_index: int = 0
    
    def load_dicom_series(self, file_paths: List[str]) -> bool:
        """
        Load a series of DICOM files.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            True if successful, False otherwise
        """
        self.slices = []
        for file_path in file_paths:
            try:
                ds = pydicom.dcmread(file_path)
                if 'PixelData' in ds:
                    self.slices.append(ds)
            except Exception as e:
                print(f"Could not read {file_path}: {e}")
                continue

        if not self.slices:
            return False

        # Sort slices by instance number or position
        try:
            self.slices.sort(key=lambda x: int(x.InstanceNumber))
        except (AttributeError, ValueError):
            try:
                self.slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
            except (AttributeError, IndexError):
                print("Warning: Could not sort slices.")

        self.current_slice_index = len(self.slices) // 2
        return True
    
    def load_dicom_folder(self, folder_path: str) -> bool:
        """
        Load all DICOM files from a folder.
        
        Args:
            folder_path: Path to folder containing DICOM files
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(folder_path):
            return False
            
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        dicom_files = [f for f in files if f.lower().endswith(('.dcm', '.dicom')) or not '.' in os.path.basename(f)]
        
        if not dicom_files:
            return False
            
        return self.load_dicom_series(dicom_files)
    
    def get_current_slice(self) -> Optional[pydicom.Dataset]:
        """Get the currently selected slice."""
        if not self.slices:
            return None
        return self.slices[self.current_slice_index]
    
    def get_pixel_data(self, slice_index: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Get pixel data for specified slice or current slice.
        
        Args:
            slice_index: Index of slice to get data for (None for current)
            
        Returns:
            Pixel data as numpy array or None if invalid
        """
        if not self.slices:
            return None
            
        if slice_index is None:
            slice_index = self.current_slice_index
            
        if slice_index < 0 or slice_index >= len(self.slices):
            return None
            
        return self.slices[slice_index].pixel_array.astype(np.float32)
    
    def get_window_level_defaults(self) -> Tuple[float, float]:
        """
        Get default window center and width for current slice.
        
        Returns:
            Tuple of (window_center, window_width)
        """
        if not self.slices:
            return 0.0, 1.0
            
        first_slice = self.slices[0]
        pixel_data = self.get_pixel_data(0)
        
        if pixel_data is None:
            return 0.0, 1.0
        
        window_center = first_slice.get("WindowCenter", pixel_data.mean())
        window_width = first_slice.get("WindowWidth", pixel_data.max() - pixel_data.min())
        
        if isinstance(window_center, pydicom.multival.MultiValue):
            window_center = window_center[0]
        if isinstance(window_width, pydicom.multival.MultiValue):
            window_width = window_width[0]
            
        return float(window_center), float(window_width)
    
    def get_pixel_spacing(self) -> Tuple[float, float]:
        """
        Get pixel spacing for measurements.
        
        Returns:
            Tuple of (row_spacing, col_spacing) in mm
        """
        if not self.slices:
            return 1.0, 1.0
            
        current_slice = self.get_current_slice()
        if current_slice is None:
            return 1.0, 1.0
            
        try:
            pixel_spacing = current_slice.PixelSpacing
            return float(pixel_spacing[0]), float(pixel_spacing[1])
        except (AttributeError, IndexError, ValueError):
            return 1.0, 1.0
    
    def get_slice_count(self) -> int:
        """Get total number of slices."""
        return len(self.slices)
    
    def set_current_slice(self, index: int) -> bool:
        """
        Set the current slice index.
        
        Args:
            index: New slice index
            
        Returns:
            True if successful, False if invalid index
        """
        if index < 0 or index >= len(self.slices):
            return False
        self.current_slice_index = index
        return True