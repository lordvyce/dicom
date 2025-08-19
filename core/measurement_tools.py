"""
Measurement Tools - Interactive measurement functionality
"""
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from typing import List, Tuple, Optional
import math


class MeasurementMode:
    """Enumeration for measurement modes."""
    NONE = 0
    DISTANCE = 1
    ANGLE = 2
    CROSSHAIR = 3


class CrosshairItem(QGraphicsItem):
    """Crosshair cursor for pixel value display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setZValue(100)  # Always on top
        self.pen = QPen(QColor(255, 255, 0), 1, Qt.SolidLine)
        self.visible = True
        
    def boundingRect(self) -> QRectF:
        return QRectF(-50, -50, 100, 100)
    
    def paint(self, painter, option, widget):
        if not self.visible:
            return
            
        painter.setPen(self.pen)
        # Draw crosshair lines
        painter.drawLine(-20, 0, 20, 0)
        painter.drawLine(0, -20, 0, 20)
        
    def set_visible(self, visible: bool):
        self.visible = visible
        self.update()


class DistanceMeasurement(QGraphicsItem):
    """Distance measurement annotation."""
    
    def __init__(self, start_point: QPointF, end_point: QPointF, 
                 distance_mm: float, parent=None):
        super().__init__(parent)
        self.start_point = start_point
        self.end_point = end_point
        self.distance_mm = distance_mm
        self.pen = QPen(QColor(0, 255, 0), 2, Qt.SolidLine)
        self.text_color = QColor(0, 255, 0)
        self.setZValue(50)
        
        # Create line and text items
        self.line_item = QGraphicsLineItem(start_point.x(), start_point.y(),
                                         end_point.x(), end_point.y(), self)
        self.line_item.setPen(self.pen)
        
        # Position text at midpoint
        mid_x = (start_point.x() + end_point.x()) / 2
        mid_y = (start_point.y() + end_point.y()) / 2
        
        self.text_item = QGraphicsTextItem(f"{distance_mm:.1f} mm", self)
        self.text_item.setPos(mid_x, mid_y - 20)
        self.text_item.setDefaultTextColor(self.text_color)
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)
        
    def boundingRect(self) -> QRectF:
        # Return bounding rect that encompasses line and text
        min_x = min(self.start_point.x(), self.end_point.x()) - 50
        max_x = max(self.start_point.x(), self.end_point.x()) + 50
        min_y = min(self.start_point.y(), self.end_point.y()) - 50
        max_y = max(self.start_point.y(), self.end_point.y()) + 50
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def paint(self, painter, option, widget):
        # Painting is handled by child items
        pass


class AngleMeasurement(QGraphicsItem):
    """Angle measurement annotation."""
    
    def __init__(self, point1: QPointF, vertex: QPointF, point2: QPointF, 
                 angle_deg: float, parent=None):
        super().__init__(parent)
        self.point1 = point1
        self.vertex = vertex
        self.point2 = point2
        self.angle_deg = angle_deg
        self.pen = QPen(QColor(255, 0, 255), 2, Qt.SolidLine)
        self.text_color = QColor(255, 0, 255)
        self.setZValue(50)
        
        # Create line items
        self.line1 = QGraphicsLineItem(vertex.x(), vertex.y(),
                                     point1.x(), point1.y(), self)
        self.line1.setPen(self.pen)
        
        self.line2 = QGraphicsLineItem(vertex.x(), vertex.y(),
                                     point2.x(), point2.y(), self)
        self.line2.setPen(self.pen)
        
        # Add angle text near vertex
        self.text_item = QGraphicsTextItem(f"{angle_deg:.1f}°", self)
        self.text_item.setPos(vertex.x() + 10, vertex.y() - 30)
        self.text_item.setDefaultTextColor(self.text_color)
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)
        
    def boundingRect(self) -> QRectF:
        # Return bounding rect that encompasses all points
        min_x = min(self.point1.x(), self.vertex.x(), self.point2.x()) - 50
        max_x = max(self.point1.x(), self.vertex.x(), self.point2.x()) + 50
        min_y = min(self.point1.y(), self.vertex.y(), self.point2.y()) - 50
        max_y = max(self.point1.y(), self.vertex.y(), self.point2.y()) + 50
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def paint(self, painter, option, widget):
        # Painting is handled by child items
        pass


class MeasurementManager:
    """Manages measurement tools and annotations."""
    
    def __init__(self, scene):
        self.scene = scene
        self.measurements: List[QGraphicsItem] = []
        self.current_mode = MeasurementMode.NONE
        
        # Crosshair
        self.crosshair = CrosshairItem()
        self.scene.addItem(self.crosshair)
        self.crosshair.set_visible(False)
        
        # Measurement state
        self.measurement_points: List[QPointF] = []
        
    def set_measurement_mode(self, mode: int):
        """Set the current measurement mode."""
        self.current_mode = mode
        self.measurement_points.clear()
        
        # Show/hide crosshair
        self.crosshair.set_visible(mode == MeasurementMode.CROSSHAIR)
    
    def update_crosshair_position(self, scene_pos: QPointF):
        """Update crosshair position."""
        if self.current_mode == MeasurementMode.CROSSHAIR:
            self.crosshair.setPos(scene_pos)
    
    def handle_click(self, scene_pos: QPointF, pixel_spacing: Tuple[float, float]) -> Optional[str]:
        """
        Handle mouse click for measurements.
        
        Args:
            scene_pos: Click position in scene coordinates
            pixel_spacing: Pixel spacing for real measurements
            
        Returns:
            Status message or None
        """
        if self.current_mode == MeasurementMode.DISTANCE:
            return self._handle_distance_click(scene_pos, pixel_spacing)
        elif self.current_mode == MeasurementMode.ANGLE:
            return self._handle_angle_click(scene_pos, pixel_spacing)
        
        return None
    
    def _handle_distance_click(self, scene_pos: QPointF, pixel_spacing: Tuple[float, float]) -> Optional[str]:
        """Handle distance measurement clicks."""
        self.measurement_points.append(scene_pos)
        
        if len(self.measurement_points) == 1:
            return "Click second point to complete distance measurement"
        elif len(self.measurement_points) == 2:
            # Calculate distance
            p1 = self.measurement_points[0]
            p2 = self.measurement_points[1]
            
            dx = (p2.x() - p1.x()) * pixel_spacing[1]
            dy = (p2.y() - p1.y()) * pixel_spacing[0]
            distance_mm = math.sqrt(dx*dx + dy*dy)
            
            # Create measurement annotation
            measurement = DistanceMeasurement(p1, p2, distance_mm)
            self.scene.addItem(measurement)
            self.measurements.append(measurement)
            
            # Reset for next measurement
            self.measurement_points.clear()
            
            return f"Distance: {distance_mm:.1f} mm"
        
        return None
    
    def _handle_angle_click(self, scene_pos: QPointF, pixel_spacing: Tuple[float, float]) -> Optional[str]:
        """Handle angle measurement clicks."""
        self.measurement_points.append(scene_pos)
        
        if len(self.measurement_points) == 1:
            return "Click vertex point"
        elif len(self.measurement_points) == 2:
            return "Click third point to complete angle measurement"
        elif len(self.measurement_points) == 3:
            # Calculate angle
            p1 = self.measurement_points[0]
            vertex = self.measurement_points[1]
            p2 = self.measurement_points[2]
            
            # Vectors from vertex
            v1x, v1y = p1.x() - vertex.x(), p1.y() - vertex.y()
            v2x, v2y = p2.x() - vertex.x(), p2.y() - vertex.y()
            
            # Calculate angle
            dot_product = v1x * v2x + v1y * v2y
            mag1 = math.sqrt(v1x*v1x + v1y*v1y)
            mag2 = math.sqrt(v2x*v2x + v2y*v2y)
            
            if mag1 > 0 and mag2 > 0:
                cos_angle = dot_product / (mag1 * mag2)
                cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp
                angle_rad = math.acos(cos_angle)
                angle_deg = math.degrees(angle_rad)
                
                # Create measurement annotation
                measurement = AngleMeasurement(p1, vertex, p2, angle_deg)
                self.scene.addItem(measurement)
                self.measurements.append(measurement)
                
                # Reset for next measurement
                self.measurement_points.clear()
                
                return f"Angle: {angle_deg:.1f}°"
        
        return None
    
    def clear_measurements(self):
        """Clear all measurements."""
        for measurement in self.measurements:
            self.scene.removeItem(measurement)
        self.measurements.clear()
        self.measurement_points.clear()
    
    def get_measurement_count(self) -> int:
        """Get number of active measurements."""
        return len(self.measurements)