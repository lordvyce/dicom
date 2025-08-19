"""
Image Processor - Handles window/level adjustments and image transformations
"""
import numpy as np
import pydicom
from PyQt5.QtGui import QImage, QPixmap
from typing import Optional, Tuple


class ImageProcessor:
    """Handles image processing operations for DICOM display."""
    
    @staticmethod
    def apply_window_level(image: np.ndarray, level: float, width: float, 
                          slope: float = 1.0, intercept: float = 0.0) -> np.ndarray:
        """
        Apply window/level transformation to image data.
        
        Args:
            image: Input image data
            level: Window level (center)
            width: Window width
            slope: Rescale slope from DICOM
            intercept: Rescale intercept from DICOM
            
        Returns:
            8-bit image data ready for display
        """
        min_val = level - width / 2
        max_val = level + width / 2
        
        # Apply rescale slope and intercept
        processed_image = image * slope + intercept
        
        # Apply windowing
        windowed_image = np.clip(processed_image, min_val, max_val)
        
        # Normalize to 8-bit
        if max_val != min_val:
            normalized_image = ((windowed_image - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
        else:
            normalized_image = np.zeros_like(windowed_image, dtype=np.uint8)

        return normalized_image
    
    @staticmethod
    def get_hounsfield_value(image: np.ndarray, x: int, y: int, 
                           slope: float = 1.0, intercept: float = 0.0) -> Optional[float]:
        """
        Get Hounsfield Unit value at specific pixel coordinates.
        
        Args:
            image: Original image data
            x, y: Pixel coordinates
            slope: Rescale slope from DICOM
            intercept: Rescale intercept from DICOM
            
        Returns:
            HU value or None if coordinates invalid
        """
        if x < 0 or y < 0 or y >= image.shape[0] or x >= image.shape[1]:
            return None
            
        pixel_value = float(image[y, x])
        hu_value = pixel_value * slope + intercept
        return hu_value
    
    @staticmethod
    def array_to_qimage(image_array: np.ndarray) -> QImage:
        """
        Convert numpy array to QImage.
        
        Args:
            image_array: 8-bit numpy array
            
        Returns:
            QImage object
        """
        height, width = image_array.shape
        return QImage(image_array.data, width, height, width, QImage.Format_Grayscale8)
    
    @staticmethod
    def qimage_to_pixmap(qimage: QImage) -> QPixmap:
        """Convert QImage to QPixmap."""
        return QPixmap.fromImage(qimage)
    
    @staticmethod
    def calculate_distance(point1: Tuple[int, int], point2: Tuple[int, int], 
                         pixel_spacing: Tuple[float, float]) -> float:
        """
        Calculate real-world distance between two points.
        
        Args:
            point1: First point (x, y)
            point2: Second point (x, y) 
            pixel_spacing: Pixel spacing (row, col) in mm
            
        Returns:
            Distance in mm
        """
        dx = (point2[0] - point1[0]) * pixel_spacing[1]  # col spacing
        dy = (point2[1] - point1[1]) * pixel_spacing[0]  # row spacing
        return np.sqrt(dx*dx + dy*dy)
    
    @staticmethod
    def calculate_angle(point1: Tuple[int, int], vertex: Tuple[int, int], 
                       point2: Tuple[int, int]) -> float:
        """
        Calculate angle between three points.
        
        Args:
            point1: First point
            vertex: Vertex point
            point2: Second point
            
        Returns:
            Angle in degrees
        """
        # Vectors from vertex to points
        v1 = np.array([point1[0] - vertex[0], point1[1] - vertex[1]])
        v2 = np.array([point2[0] - vertex[0], point2[1] - vertex[1]])
        
        # Calculate angle using dot product
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Handle numerical errors
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg