"""
DICOM Viewer v3.0 - Professional Foundations

This version is a significant architectural refactor to support advanced features.

New Features:
- QGraphicsView/Scene for interactive Zoom (mouse wheel) and Pan (middle-click drag).
- Professional dark mode theme using QSS stylesheets.
- Window/Level presets for common tissues (Bone, Lung, Soft Tissue).
- Keyboard shortcuts for slice navigation (Left/Right arrow keys).

Retained Features:
- Loading single files and DICOM series.
- Interactive window/level adjustment with sliders and mouse drag.
- Metadata display.

Dependencies:
pip install PyQt5 pydicom numpy pylibjpeg pylibjpeg-libjpeg
"""
import sys
import os
import pydicom
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QFrame, QStatusBar, QAction, QMenuBar, QToolBar,
    QButtonGroup, QScrollArea, QSplitter, QTabWidget, QGroupBox
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QIcon, QFont, QPixmap as QPixmapIcon, QTransform
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF, QTimer, QSize

# --- Icon Creation Helper ---
def create_icon(icon_type, size=16, color="#E0E0E0"):
    """Create simple icons programmatically."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Set pen and brush
    from PyQt5.QtGui import QPen, QBrush, QColor
    pen = QPen(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.setBrush(QBrush(QColor(color)))
    
    margin = 2
    inner_size = size - 2 * margin
    
    if icon_type == "open_file":
        # File icon
        painter.drawRect(margin + 2, margin, inner_size - 4, inner_size - 2)
        painter.drawLine(margin + 2, margin + 3, margin + inner_size - 2, margin + 3)
        painter.drawLine(margin + 2, margin + 6, margin + inner_size - 2, margin + 6)
        painter.drawLine(margin + 2, margin + 9, margin + inner_size - 2, margin + 9)
    elif icon_type == "open_folder":
        # Folder icon
        painter.drawRect(margin, margin + 3, inner_size, inner_size - 6)
        painter.drawRect(margin, margin, inner_size // 2, 3)
    elif icon_type == "zoom_in":
        # Magnifying glass with +
        center = size // 2
        radius = size // 3
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        painter.drawLine(center + radius - 1, center + radius - 1, size - margin, size - margin)
        painter.drawLine(center - 2, center, center + 2, center)
        painter.drawLine(center, center - 2, center, center + 2)
    elif icon_type == "zoom_out":
        # Magnifying glass with -
        center = size // 2
        radius = size // 3
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        painter.drawLine(center + radius - 1, center + radius - 1, size - margin, size - margin)
        painter.drawLine(center - 2, center, center + 2, center)
    elif icon_type == "fit_window":
        # Fit to window icon
        painter.drawRect(margin, margin, inner_size, inner_size)
        painter.drawLine(margin + 2, margin + 2, margin + inner_size - 2, margin + 2)
        painter.drawLine(margin + 2, margin + inner_size - 2, margin + inner_size - 2, margin + inner_size - 2)
    elif icon_type == "export":
        # Export/save icon
        painter.drawRect(margin + 2, margin, inner_size - 4, inner_size - 4)
        painter.drawLine(margin + 4, margin + inner_size - 2, margin + inner_size - 2, margin + inner_size - 2)
        painter.drawPolygon([
            QPoint(size // 2 - 1, margin + inner_size - 6),
            QPoint(size // 2 + 1, margin + inner_size - 6),
            QPoint(size // 2, margin + inner_size - 4)
        ])
    elif icon_type == "measure":
        # Ruler/measure icon
        painter.drawLine(margin, margin, margin + inner_size, margin + inner_size)
        for i in range(0, inner_size, 3):
            painter.drawLine(margin + i, margin + i - 2, margin + i, margin + i + 2)
    elif icon_type == "theme":
        # Theme toggle icon (sun/moon)
        center = size // 2
        radius = size // 4
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        # Rays
        ray_length = 3
        for angle in range(0, 360, 45):
            import math
            x1 = center + (radius + 1) * math.cos(math.radians(angle))
            y1 = center + (radius + 1) * math.sin(math.radians(angle))
            x2 = center + (radius + 1 + ray_length) * math.cos(math.radians(angle))
            y2 = center + (radius + 1 + ray_length) * math.sin(math.radians(angle))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    painter.end()
    return QIcon(pixmap)


# --- Enhanced UI Components ---
class ModernGroupBox(QGroupBox):
    """A modern styled group box with better visual hierarchy."""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setMinimumHeight(80)


class StatusIndicator(QLabel):
    """A status indicator widget for showing current state."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(24)
        self.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }
        """)
    
    def set_status(self, text, status_type="info"):
        self.setText(text)
        colors = {
            "info": "rgba(74, 158, 255, 0.2)",
            "success": "rgba(40, 167, 69, 0.2)", 
            "warning": "rgba(255, 193, 7, 0.2)",
            "error": "rgba(220, 53, 69, 0.2)"
        }
        border_colors = {
            "info": "rgba(74, 158, 255, 0.4)",
            "success": "rgba(40, 167, 69, 0.4)",
            "warning": "rgba(255, 193, 7, 0.4)", 
            "error": "rgba(220, 53, 69, 0.4)"
        }
        self.setStyleSheet(f"""
            QLabel {{
                background: {colors.get(status_type, colors["info"])};
                border: 1px solid {border_colors.get(status_type, border_colors["info"])};
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
        """)


# --- Constants ---

DARK_THEME = """
/* Main Application Styling with Glassmorphism */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                               stop:0 #1a1a1a, stop:1 #2d2d2d);
    color: #E0E0E0;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    background-color: transparent;
    color: #E0E0E0;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* Modern Buttons with Glassmorphism */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(255, 255, 255, 0.1),
                               stop:1 rgba(255, 255, 255, 0.05));
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 8px 16px;
    min-width: 100px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(255, 255, 255, 0.15),
                               stop:1 rgba(255, 255, 255, 0.08));
    border: 1px solid rgba(255, 255, 255, 0.3);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(255, 255, 255, 0.05),
                               stop:1 rgba(255, 255, 255, 0.02));
    border: 1px solid rgba(255, 255, 255, 0.1);
}

QPushButton:disabled {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: #666666;
}

/* Control Panels */
QGroupBox {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 rgba(255, 255, 255, 0.03),
                               stop:1 rgba(255, 255, 255, 0.01));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    margin-top: 1ex;
    padding-top: 10px;
    font-weight: 600;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #FFFFFF;
}

/* Enhanced Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 rgba(255, 255, 255, 0.1),
                               stop:1 rgba(255, 255, 255, 0.05));
    margin: 2px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #4A9EFF, stop:1 #2E7AE4);
    border: 2px solid rgba(255, 255, 255, 0.3);
    width: 18px;
    margin: -6px 0;
    border-radius: 11px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #5AAFFF, stop:1 #3E8AE4);
    border: 2px solid rgba(255, 255, 255, 0.5);
}

QSlider::handle:horizontal:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #3A8EEF, stop:1 #1E6AD4);
}

/* Labels */
QLabel {
    font-size: 13px;
    color: #E0E0E0;
    font-weight: 400;
}

/* Graphics View */
QGraphicsView {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #0a0a0a, stop:1 #1a1a1a);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

/* Status Bar */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 rgba(255, 255, 255, 0.05),
                               stop:1 rgba(255, 255, 255, 0.02));
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding: 4px;
    font-size: 12px;
}

/* Separators */
QFrame[frameShape="4"] {
    color: rgba(255, 255, 255, 0.2);
    background-color: rgba(255, 255, 255, 0.2);
    max-height: 1px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: rgba(255, 255, 255, 0.05);
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.3);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Tooltips */
QToolTip {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 rgba(50, 50, 50, 0.95),
                               stop:1 rgba(30, 30, 30, 0.95));
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    padding: 6px;
    font-size: 12px;
    color: #FFFFFF;
}
"""

LIGHT_THEME = """
/* Light Theme */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                               stop:0 #f8f9fa, stop:1 #e9ecef);
    color: #212529;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    background-color: transparent;
    color: #212529;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(0, 0, 0, 0.05),
                               stop:1 rgba(0, 0, 0, 0.02));
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    min-width: 100px;
    font-weight: 500;
    font-size: 13px;
    color: #212529;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(0, 0, 0, 0.08),
                               stop:1 rgba(0, 0, 0, 0.04));
    border: 1px solid rgba(0, 0, 0, 0.15);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 rgba(0, 0, 0, 0.02),
                               stop:1 rgba(0, 0, 0, 0.01));
}

QGroupBox {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 rgba(0, 0, 0, 0.02),
                               stop:1 rgba(0, 0, 0, 0.01));
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    margin-top: 1ex;
    padding-top: 10px;
    font-weight: 600;
    font-size: 14px;
    color: #212529;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #212529;
}

QGraphicsView {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 #ffffff, stop:1 #f8f9fa);
    border: 2px solid rgba(0, 0, 0, 0.1);
    border-radius: 8px;
}

QLabel {
    font-size: 13px;
    color: #212529;
    font-weight: 400;
}

QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 rgba(0, 0, 0, 0.03),
                               stop:1 rgba(0, 0, 0, 0.01));
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    padding: 4px;
    font-size: 12px;
    color: #212529;
}
"""

PRESETS = {
    "Soft Tissue": {"level": 40, "width": 400},
    "Lung": {"level": -600, "width": 1500},
    "Bone": {"level": 500, "width": 2000},
}


# --- Custom Graphics View for Zoom/Pan ---

class DicomGraphicsView(QGraphicsView):
    """A QGraphicsView subclass for advanced interaction like zoom and pan."""
    windowLevelChanged = pyqtSignal(int, int)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self._is_adjusting_wl = False
        self._last_mouse_pos = QPoint()

    def wheelEvent(self, event):
        """Zoom in or out with the mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event):
        """Handle mouse press for window/level or panning."""
        if event.button() == Qt.LeftButton:
            self._is_adjusting_wl = True
            self._last_mouse_pos = event.pos()
        else:
            super().mousePressEvent(event) # Propagate for panning

    def mouseMoveEvent(self, event):
        """Handle mouse move for window/level adjustment."""
        if self._is_adjusting_wl:
            delta = event.pos() - self._last_mouse_pos
            level_change = delta.y()
            width_change = delta.x()
            self.windowLevelChanged.emit(level_change, width_change)
            self._last_mouse_pos = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset flags on mouse release."""
        if event.button() == Qt.LeftButton:
            self._is_adjusting_wl = False
        super().mouseReleaseEvent(event)


# --- Main Application Window ---

class DicomViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DICOM Viewer v4.0 - Professional Edition")
        self.setGeometry(100, 100, 1400, 1000)
        self.setMinimumSize(1200, 800)

        # Data
        self.slices = []
        self.current_slice_index = 0
        self.current_theme = "dark"
        self.recent_files = []
        self.max_recent_files = 10
        
        # Image transformation state
        self.rotation_angle = 0
        self.flip_horizontal_state = False
        self.flip_vertical_state = False
        
        # Settings file path
        import os
        self.settings_file = os.path.expanduser("~/.dicom_viewer_settings.json")
        self.load_settings()

        # Initialize UI
        self.init_ui()
        self.init_status_bar()
        self.init_menu_bar()
        
        # Timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second

    def init_ui(self):
        """Initialize the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main splitter for resizable panels
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        central_widget_layout.setContentsMargins(8, 8, 8, 8)

        # Left Panel (Controls) - Make it scrollable
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)
        
        # Right Panel (Image Display)
        right_panel = self.create_image_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([350, 1050])  # Left panel smaller, image panel larger
        main_splitter.setCollapsible(0, False)  # Don't allow left panel to be completely collapsed

    def create_control_panel(self):
        """Create the left control panel with modern styling."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(340)
        scroll_area.setMaximumWidth(400)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(12, 12, 12, 12)

        # File Operations Group
        file_group = ModernGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.btn_open_file = QPushButton(" Open DICOM File")
        self.btn_open_file.setIcon(create_icon("open_file"))
        self.btn_open_file.setToolTip("Open a single DICOM file")
        self.btn_open_file.clicked.connect(self.open_file)
        
        self.btn_open_folder = QPushButton(" Open DICOM Series")
        self.btn_open_folder.setIcon(create_icon("open_folder"))
        self.btn_open_folder.setToolTip("Open a folder containing DICOM series")
        self.btn_open_folder.clicked.connect(self.open_folder)
        
        file_layout.addWidget(self.btn_open_file)
        file_layout.addWidget(self.btn_open_folder)
        controls_layout.addWidget(file_group)

        # Slice Navigation Group
        slice_group = ModernGroupBox("Slice Navigation")
        slice_layout = QVBoxLayout(slice_group)
        
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self.slice_slider_changed)
        self.slice_label = QLabel("Slice: N/A")
        self.slice_label.setAlignment(Qt.AlignCenter)
        
        slice_layout.addWidget(self.slice_label)
        slice_layout.addWidget(self.slice_slider)
        controls_layout.addWidget(slice_group)

        # Window/Level Controls Group
        wl_group = ModernGroupBox("Window & Level")
        wl_layout = QVBoxLayout(wl_group)
        
        self.level_slider = QSlider(Qt.Horizontal)
        self.level_slider.setEnabled(False)
        self.level_slider.valueChanged.connect(self.update_image)
        self.level_label = QLabel("Level: N/A")
        self.level_label.setAlignment(Qt.AlignCenter)
        
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setEnabled(False)
        self.width_slider.valueChanged.connect(self.update_image)
        self.width_label = QLabel("Width: N/A")
        self.width_label.setAlignment(Qt.AlignCenter)
        
        wl_layout.addWidget(self.level_label)
        wl_layout.addWidget(self.level_slider)
        wl_layout.addWidget(self.width_label)
        wl_layout.addWidget(self.width_slider)
        controls_layout.addWidget(wl_group)

        # Window/Level Presets Group
        presets_group = ModernGroupBox("Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_buttons_layout = QHBoxLayout()
        for name, values in PRESETS.items():
            btn = QPushButton(name)
            btn.setToolTip(f"Apply {name} window/level preset")
            btn.clicked.connect(lambda _, v=values: self.apply_preset(v))
            preset_buttons_layout.addWidget(btn)
        
        presets_layout.addLayout(preset_buttons_layout)
        controls_layout.addWidget(presets_group)

        # Tools Group
        tools_group = ModernGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)
        
        tools_row1 = QHBoxLayout()
        self.btn_zoom_fit = QPushButton(" Fit")
        self.btn_zoom_fit.setIcon(create_icon("fit_window"))
        self.btn_zoom_fit.setToolTip("Fit image to window")
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)
        
        self.btn_zoom_in = QPushButton(" Zoom +")
        self.btn_zoom_in.setIcon(create_icon("zoom_in"))
        self.btn_zoom_in.setToolTip("Zoom in")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        
        self.btn_zoom_out = QPushButton(" Zoom -")
        self.btn_zoom_out.setIcon(create_icon("zoom_out"))
        self.btn_zoom_out.setToolTip("Zoom out")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        tools_row1.addWidget(self.btn_zoom_fit)
        tools_row1.addWidget(self.btn_zoom_in)
        tools_row1.addWidget(self.btn_zoom_out)
        
        tools_row2 = QHBoxLayout()
        self.btn_export = QPushButton(" Export")
        self.btn_export.setIcon(create_icon("export"))
        self.btn_export.setToolTip("Export current image")
        self.btn_export.clicked.connect(self.export_image)
        self.btn_export.setEnabled(False)
        
        self.btn_measure = QPushButton(" Measure")
        self.btn_measure.setIcon(create_icon("measure"))
        self.btn_measure.setToolTip("Distance measurement tool")
        self.btn_measure.clicked.connect(self.toggle_measure_mode)
        self.btn_measure.setEnabled(False)
        
        self.btn_theme = QPushButton(" Theme")
        self.btn_theme.setIcon(create_icon("theme"))
        self.btn_theme.setToolTip("Toggle dark/light theme")
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        tools_row2.addWidget(self.btn_export)
        tools_row2.addWidget(self.btn_measure)
        tools_row2.addWidget(self.btn_theme)
        
        tools_layout.addLayout(tools_row1)
        tools_layout.addLayout(tools_row2)
        controls_layout.addWidget(tools_group)

        # Patient Information Group
        info_group = ModernGroupBox("Patient Information")
        info_layout = QVBoxLayout(info_group)
        
        self.metadata_label = QLabel("No DICOM file loaded")
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setAlignment(Qt.AlignTop)
        self.metadata_label.setMinimumHeight(120)
        
        info_layout.addWidget(self.metadata_label)
        controls_layout.addWidget(info_group)

        controls_layout.addStretch()
        scroll_area.setWidget(controls_widget)
        return scroll_area

    def create_image_panel(self):
        """Create the right image display panel."""
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image display area
        self.scene = QGraphicsScene()
        self.view = DicomGraphicsView(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.view.windowLevelChanged.connect(self.handle_mouse_wl_adjust)
        
        image_layout.addWidget(self.view)
        return image_widget

    def init_status_bar(self):
        """Initialize the status bar with modern indicators."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status indicators
        self.status_file = StatusIndicator()
        self.status_file.set_status("No file loaded", "info")
        
        self.status_zoom = StatusIndicator()
        self.status_zoom.set_status("Zoom: 100%", "info")
        
        self.status_position = StatusIndicator()
        self.status_position.set_status("Position: (0, 0)", "info")
        
        self.status_pixel = StatusIndicator()
        self.status_pixel.set_status("Pixel: N/A", "info")
        
        # Add permanent widgets to status bar
        self.status_bar.addPermanentWidget(self.status_file)
        self.status_bar.addPermanentWidget(self.status_zoom)
        self.status_bar.addPermanentWidget(self.status_position)
        self.status_bar.addPermanentWidget(self.status_pixel)
        
        self.status_bar.showMessage("Ready - Load a DICOM file to begin")

    def init_menu_bar(self):
        """Initialize the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_file_action = QAction('Open File...', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.setToolTip('Open a single DICOM file')
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        open_folder_action = QAction('Open Folder...', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.setToolTip('Open a folder containing DICOM series')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Recent Files submenu
        self.recent_files_menu = file_menu.addMenu('Recent Files')
        self.update_recent_files_menu()
        
        file_menu.addSeparator()
        
        export_action = QAction('Export Image...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.setToolTip('Export current image to file')
        export_action.triggered.connect(self.export_image)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        zoom_fit_action = QAction('Fit to Window', self)
        zoom_fit_action.setShortcut('F')
        zoom_fit_action.setToolTip('Fit image to window')
        zoom_fit_action.triggered.connect(self.zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        zoom_100_action = QAction('Actual Size', self)
        zoom_100_action.setShortcut('Ctrl+1')
        zoom_100_action.setToolTip('Reset zoom to 100%')
        zoom_100_action.triggered.connect(self.zoom_actual)
        view_menu.addAction(zoom_100_action)
        
        zoom_in_action = QAction('Zoom In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.setToolTip('Zoom in')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.setToolTip('Zoom out')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        # Window/Level presets submenu
        presets_menu = view_menu.addMenu('Window/Level Presets')
        for name, values in PRESETS.items():
            action = QAction(name, self)
            action.setToolTip(f"Apply {name} window/level preset")
            action.triggered.connect(lambda checked, v=values: self.apply_preset(v))
            presets_menu.addAction(action)
        
        view_menu.addSeparator()
        
        theme_action = QAction('Toggle Theme', self)
        theme_action.setShortcut('Ctrl+T')
        theme_action.setToolTip('Switch between dark and light themes')
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        measure_action = QAction('Distance Measurement', self)
        measure_action.setShortcut('M')
        measure_action.setToolTip('Measure distances in the image')
        measure_action.triggered.connect(self.toggle_measure_mode)
        tools_menu.addAction(measure_action)
        
        rotate_cw_action = QAction('Rotate Clockwise', self)
        rotate_cw_action.setShortcut('R')
        rotate_cw_action.setToolTip('Rotate image 90° clockwise')
        rotate_cw_action.triggered.connect(self.rotate_clockwise)
        tools_menu.addAction(rotate_cw_action)
        
        rotate_ccw_action = QAction('Rotate Counter-clockwise', self)
        rotate_ccw_action.setShortcut('Shift+R')
        rotate_ccw_action.setToolTip('Rotate image 90° counter-clockwise')
        rotate_ccw_action.triggered.connect(self.rotate_counterclockwise)
        tools_menu.addAction(rotate_ccw_action)
        
        flip_h_action = QAction('Flip Horizontal', self)
        flip_h_action.setShortcut('H')
        flip_h_action.setToolTip('Flip image horizontally')
        flip_h_action.triggered.connect(self.flip_horizontal)
        tools_menu.addAction(flip_h_action)
        
        flip_v_action = QAction('Flip Vertical', self)
        flip_v_action.setShortcut('V')
        flip_v_action.setToolTip('Flip image vertically')
        flip_v_action.triggered.connect(self.flip_vertical)
        tools_menu.addAction(flip_v_action)
        
        tools_menu.addSeparator()
        
        reset_transform_action = QAction('Reset Transformations', self)
        reset_transform_action.setShortcut('Ctrl+R')
        reset_transform_action.setToolTip('Reset all image transformations')
        reset_transform_action.triggered.connect(self.reset_transformations)
        tools_menu.addAction(reset_transform_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        shortcuts_action = QAction('Keyboard Shortcuts', self)
        shortcuts_action.setShortcut('F1')
        shortcuts_action.triggered.connect(self.show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction('About DICOM Viewer', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def update_status(self):
        """Update status bar information."""
        if self.view and self.view.transform():
            # Update zoom level
            scale = self.view.transform().m11()  # Get scaling factor
            zoom_percent = int(scale * 100)
            self.status_zoom.set_status(f"Zoom: {zoom_percent}%", "info")
        
        # Update file status
        if self.slices:
            filename = "DICOM Series" if len(self.slices) > 1 else "DICOM File"
            self.status_file.set_status(f"Loaded: {filename}", "success")
        else:
            self.status_file.set_status("No file loaded", "info")

    def zoom_fit(self):
        """Fit image to window."""
        if self.pixmap_item.pixmap():
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self.update_status()

    def zoom_in(self):
        """Zoom in by 25%."""
        self.view.scale(1.25, 1.25)
        self.update_status()

    def zoom_out(self):
        """Zoom out by 25%."""
        self.view.scale(0.8, 0.8)
        self.update_status()

    def zoom_actual(self):
        """Reset zoom to 100%."""
        self.view.resetTransform()
        self.update_status()

    def export_image(self):
        """Export current image to file."""
        if not self.slices:
            self.status_bar.showMessage("No image to export", 3000)
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Image", 
            f"dicom_slice_{self.current_slice_index + 1}.png",
            "PNG Files (*.png);;JPEG Files (*.jpg);;TIFF Files (*.tiff);;All Files (*)"
        )
        
        if filename:
            try:
                # Get current image
                pixmap = self.pixmap_item.pixmap()
                if pixmap:
                    pixmap.save(filename)
                    self.status_bar.showMessage(f"Image exported to {filename}", 3000)
                else:
                    self.status_bar.showMessage("Failed to export image", 3000)
            except Exception as e:
                self.status_bar.showMessage(f"Export failed: {str(e)}", 3000)

    def toggle_measure_mode(self):
        """Toggle measurement mode (placeholder for future implementation)."""
        self.status_bar.showMessage("Measurement tool - Coming soon in next update!", 3000)

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.current_theme = "light"
            QApplication.instance().setStyleSheet(LIGHT_THEME)
            self.status_bar.showMessage("Switched to light theme", 2000)
        else:
            self.current_theme = "dark"
            QApplication.instance().setStyleSheet(DARK_THEME)
            self.status_bar.showMessage("Switched to dark theme", 2000)
        
        # Update icon colors based on theme
        color = "#212529" if self.current_theme == "light" else "#E0E0E0"
        self.btn_open_file.setIcon(create_icon("open_file", color=color))
        self.btn_open_folder.setIcon(create_icon("open_folder", color=color))
        self.btn_zoom_fit.setIcon(create_icon("fit_window", color=color))
        self.btn_zoom_in.setIcon(create_icon("zoom_in", color=color))
        self.btn_zoom_out.setIcon(create_icon("zoom_out", color=color))
        self.btn_export.setIcon(create_icon("export", color=color))
        self.btn_measure.setIcon(create_icon("measure", color=color))
        self.btn_theme.setIcon(create_icon("theme", color=color))

    def load_settings(self):
        """Load application settings from file."""
        try:
            import json
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.recent_files = settings.get('recent_files', [])
                    self.current_theme = settings.get('theme', 'dark')
        except Exception as e:
            print(f"Could not load settings: {e}")
            self.recent_files = []

    def save_settings(self):
        """Save application settings to file."""
        try:
            import json
            settings = {
                'recent_files': self.recent_files,
                'theme': self.current_theme,
                'window_geometry': {
                    'x': self.x(),
                    'y': self.y(),
                    'width': self.width(),
                    'height': self.height()
                }
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Could not save settings: {e}")

    def add_to_recent_files(self, file_path):
        """Add a file to the recent files list."""
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Add to beginning
        self.recent_files.insert(0, file_path)
        
        # Limit to max recent files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        # Update menu
        self.update_recent_files_menu()
        
        # Save settings
        self.save_settings()

    def update_recent_files_menu(self):
        """Update the recent files menu."""
        if hasattr(self, 'recent_files_menu'):
            self.recent_files_menu.clear()
            
            if self.recent_files:
                for i, file_path in enumerate(self.recent_files):
                    if i < 9:  # Only show first 9 with numbers
                        action = QAction(f"&{i+1} {os.path.basename(file_path)}", self)
                        action.setToolTip(file_path)
                    else:
                        action = QAction(os.path.basename(file_path), self)
                        action.setToolTip(file_path)
                    
                    action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
                    self.recent_files_menu.addAction(action)
                
                self.recent_files_menu.addSeparator()
                clear_action = QAction('Clear Recent Files', self)
                clear_action.triggered.connect(self.clear_recent_files)
                self.recent_files_menu.addAction(clear_action)
            else:
                no_files_action = QAction('No Recent Files', self)
                no_files_action.setEnabled(False)
                self.recent_files_menu.addAction(no_files_action)

    def open_recent_file(self, file_path):
        """Open a file from the recent files list."""
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                self.load_dicom_series([file_path])
            else:
                # It's a directory
                files = [os.path.join(file_path, f) for f in os.listdir(file_path)]
                dicom_files = [f for f in files if f.lower().endswith(('.dcm', '.dicom')) or not '.' in os.path.basename(f)]
                if dicom_files:
                    self.load_dicom_series(dicom_files)
                else:
                    self.status_bar.showMessage("No DICOM files found in recent folder", 3000)
        else:
            self.status_bar.showMessage(f"File not found: {file_path}", 3000)
            # Remove from recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                self.update_recent_files_menu()
                self.save_settings()

    def rotate_clockwise(self):
        """Rotate image 90 degrees clockwise."""
        if not self.slices:
            return
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_image()
        self.status_bar.showMessage(f"Rotated clockwise - Total rotation: {self.rotation_angle}°", 2000)

    def rotate_counterclockwise(self):
        """Rotate image 90 degrees counter-clockwise."""
        if not self.slices:
            return
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.update_image()
        self.status_bar.showMessage(f"Rotated counter-clockwise - Total rotation: {self.rotation_angle}°", 2000)

    def flip_horizontal(self):
        """Flip image horizontally."""
        if not self.slices:
            return
        self.flip_horizontal_state = not self.flip_horizontal_state
        self.update_image()
        status = "enabled" if self.flip_horizontal_state else "disabled"
        self.status_bar.showMessage(f"Horizontal flip {status}", 2000)

    def flip_vertical(self):
        """Flip image vertically."""
        if not self.slices:
            return
        self.flip_vertical_state = not self.flip_vertical_state
        self.update_image()
        status = "enabled" if self.flip_vertical_state else "disabled"
        self.status_bar.showMessage(f"Vertical flip {status}", 2000)

    def reset_transformations(self):
        """Reset all image transformations."""
        if not self.slices:
            return
        self.rotation_angle = 0
        self.flip_horizontal_state = False
        self.flip_vertical_state = False
        self.update_image()
        self.status_bar.showMessage("All transformations reset", 2000)

    def show_shortcuts_dialog(self):
        """Show keyboard shortcuts dialog."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setModal(True)
        dialog.resize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml("""
        <h2>DICOM Viewer Keyboard Shortcuts</h2>
        
        <h3>File Operations</h3>
        <b>Ctrl+O</b> - Open DICOM file<br>
        <b>Ctrl+Shift+O</b> - Open DICOM folder<br>
        <b>Ctrl+E</b> - Export current image<br>
        <b>Ctrl+Q</b> - Exit application<br>
        
        <h3>Navigation</h3>
        <b>Left/Right Arrow</b> - Previous/Next slice<br>
        <b>Up/Down Arrow</b> - Previous/Next slice<br>
        <b>Page Up/Down</b> - Jump 10% of slices<br>
        <b>Home/End</b> - First/Last slice<br>
        
        <h3>Zoom & View</h3>
        <b>F</b> - Fit image to window<br>
        <b>Ctrl+1</b> - Actual size (100%)<br>
        <b>Ctrl++</b> - Zoom in<br>
        <b>Ctrl+-</b> - Zoom out<br>
        <b>Escape</b> - Reset zoom to fit<br>
        
        <h3>Window/Level</h3>
        <b>W</b> - Increase width (contrast)<br>
        <b>Shift+W</b> - Decrease width<br>
        <b>L</b> - Increase level (brightness)<br>
        <b>Shift+L</b> - Decrease level<br>
        
        <h3>Presets</h3>
        <b>1</b> - Soft Tissue preset<br>
        <b>2</b> - Lung preset<br>
        <b>3</b> - Bone preset<br>
        
        <h3>Image Transformation</h3>
        <b>R</b> - Rotate clockwise<br>
        <b>Shift+R</b> - Rotate counter-clockwise<br>
        <b>H</b> - Flip horizontal<br>
        <b>V</b> - Flip vertical<br>
        <b>Ctrl+R</b> - Reset all transformations<br>
        
        <h3>Tools</h3>
        <b>M</b> - Measurement tool<br>
        <b>Ctrl+T</b> - Toggle theme<br>
        <b>Space</b> - Cine mode (coming soon)<br>
        
        <h3>Help</h3>
        <b>F1</b> - Show this dialog<br>
        """)
        
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()

    def show_about_dialog(self):
        """Show about dialog."""
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.about(self, "About DICOM Viewer", 
                         """<h2>DICOM Viewer v4.0</h2>
                         <p><b>Professional Medical Imaging Software</b></p>
                         
                         <p>A modern, feature-rich DICOM viewer designed for medical professionals, 
                         students, and researchers.</p>
                         
                         <h3>Features:</h3>
                         <ul>
                         <li>Modern glassmorphism UI design</li>
                         <li>Support for single files and DICOM series</li>
                         <li>Interactive zoom, pan, and window/level adjustment</li>
                         <li>Image transformations (rotate, flip)</li>
                         <li>Multiple window/level presets</li>
                         <li>Dark and light themes</li>
                         <li>Comprehensive keyboard shortcuts</li>
                         <li>Recent files management</li>
                         <li>Image export functionality</li>
                         <li>Professional metadata display</li>
                         </ul>
                         
                         <p><b>Dependencies:</b> PyQt5, pydicom, numpy</p>
                         <p><b>License:</b> Open Source</p>
                         """)

    def closeEvent(self, event):
        """Handle application close event."""
        self.save_settings()
        event.accept()

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for slice navigation and other functions."""
        if not self.slices and event.key() not in [Qt.Key_F1]:  # Allow F1 even without slices
            return
            
        # Slice navigation
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
            if self.slice_slider.isEnabled():
                self.slice_slider.setValue(min(self.slice_slider.maximum(), self.slice_slider.value() + 1))
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
            if self.slice_slider.isEnabled():
                self.slice_slider.setValue(max(self.slice_slider.minimum(), self.slice_slider.value() - 1))
        
        # Page Up/Down for faster navigation
        elif event.key() == Qt.Key_PageDown:
            if self.slice_slider.isEnabled():
                step = max(1, len(self.slices) // 10)  # Jump by 10% of total slices
                self.slice_slider.setValue(min(self.slice_slider.maximum(), self.slice_slider.value() + step))
        elif event.key() == Qt.Key_PageUp:
            if self.slice_slider.isEnabled():
                step = max(1, len(self.slices) // 10)
                self.slice_slider.setValue(max(self.slice_slider.minimum(), self.slice_slider.value() - step))
        
        # Home/End for first/last slice
        elif event.key() == Qt.Key_Home:
            if self.slice_slider.isEnabled():
                self.slice_slider.setValue(self.slice_slider.minimum())
        elif event.key() == Qt.Key_End:
            if self.slice_slider.isEnabled():
                self.slice_slider.setValue(self.slice_slider.maximum())
        
        # Space bar for play/pause (future cine mode)
        elif event.key() == Qt.Key_Space:
            self.status_bar.showMessage("Cine mode - Coming in next update!", 2000)
        
        # Window/Level adjustments with keyboard
        elif event.key() == Qt.Key_W:
            # Increase width
            new_value = min(self.width_slider.maximum(), self.width_slider.value() + 10)
            self.width_slider.setValue(new_value)
        elif event.key() == Qt.Key_Shift and event.key() == Qt.Key_W:
            # Decrease width
            new_value = max(self.width_slider.minimum(), self.width_slider.value() - 10)
            self.width_slider.setValue(new_value)
        elif event.key() == Qt.Key_L:
            # Increase level
            new_value = min(self.level_slider.maximum(), self.level_slider.value() + 10)
            self.level_slider.setValue(new_value)
        elif event.key() == Qt.Key_Shift and event.key() == Qt.Key_L:
            # Decrease level
            new_value = max(self.level_slider.minimum(), self.level_slider.value() - 10)
            self.level_slider.setValue(new_value)
        
        # Preset shortcuts
        elif event.key() == Qt.Key_1:
            self.apply_preset(PRESETS["Soft Tissue"])
        elif event.key() == Qt.Key_2:
            self.apply_preset(PRESETS["Lung"])
        elif event.key() == Qt.Key_3:
            self.apply_preset(PRESETS["Bone"])
        
        # ESC to reset zoom
        elif event.key() == Qt.Key_Escape:
            self.zoom_fit()
        
        # Other shortcuts are handled by menu actions
        else:
            super().keyPressEvent(event)

    # ... (All other methods like open_file, open_folder, load_dicom_series, etc. remain here) ...
    # Note: These methods are largely unchanged from v2, but are included below for completeness.
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open DICOM File", "", "DICOM Files (*.dcm; *.dicom)")
        if file_path:
            self.load_dicom_series([file_path])
            self.add_to_recent_files(file_path)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open DICOM Folder")
        if folder_path:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
            dicom_files = [f for f in files if f.lower().endswith(('.dcm', '.dicom')) or not '.' in os.path.basename(f)]
            
            if dicom_files:
                self.load_dicom_series(dicom_files)
                self.add_to_recent_files(folder_path)
            else:
                self.metadata_label.setText("No DICOM files found.")

    def load_dicom_series(self, file_paths):
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
            self.metadata_label.setText("Failed to load valid DICOM data.")
            return

        try:
            self.slices.sort(key=lambda x: int(x.InstanceNumber))
        except (AttributeError, ValueError):
            try:
                self.slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
            except (AttributeError, IndexError):
                print("Warning: Could not sort slices.")

        self.current_slice_index = len(self.slices) // 2
        
        # Reset transformations when loading new series
        self.rotation_angle = 0
        self.flip_horizontal_state = False
        self.flip_vertical_state = False
        
        self.setup_sliders()
        self.update_metadata()
        self.update_image()
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def setup_sliders(self):
        is_series = len(self.slices) > 1
        self.slice_slider.setEnabled(is_series)
        if is_series:
            self.slice_slider.setRange(0, len(self.slices) - 1)
            self.slice_slider.setValue(self.current_slice_index)
        
        first_slice = self.slices[0]
        pixel_data = first_slice.pixel_array.astype(np.float32)

        window_center = first_slice.get("WindowCenter", pixel_data.mean())
        window_width = first_slice.get("WindowWidth", pixel_data.max() - pixel_data.min())
        
        if isinstance(window_center, pydicom.multival.MultiValue): window_center = window_center[0]
        if isinstance(window_width, pydicom.multival.MultiValue): window_width = window_width[0]

        data_min, data_max = pixel_data.min(), pixel_data.max()
        
        self.level_slider.setRange(int(data_min), int(data_max))
        self.width_slider.setRange(1, int(data_max - data_min))
        
        self.level_slider.setValue(int(window_center))
        self.width_slider.setValue(int(window_width))
        
        # Update labels
        self.level_label.setText(f"Level: {int(window_center)}")
        self.width_label.setText(f"Width: {int(window_width)}")
        
        self.level_slider.setEnabled(True)
        self.width_slider.setEnabled(True)
        
        # Enable tools
        self.btn_export.setEnabled(True)
        self.btn_measure.setEnabled(True)

    def slice_slider_changed(self, value):
        self.current_slice_index = value
        self.update_metadata()
        self.update_image()

    def update_metadata(self):
        if not self.slices: return
        dataset = self.slices[self.current_slice_index]
        
        # Enhanced metadata display
        patient_name = dataset.get('PatientName', 'N/A')
        patient_id = dataset.get('PatientID', 'N/A')
        study_date = dataset.get('StudyDate', 'N/A')
        study_time = dataset.get('StudyTime', 'N/A')
        modality = dataset.get('Modality', 'N/A')
        institution = dataset.get('InstitutionName', 'N/A')
        
        # Format study date and time
        if study_date != 'N/A' and len(study_date) == 8:
            formatted_date = f"{study_date[:4]}-{study_date[4:6]}-{study_date[6:8]}"
        else:
            formatted_date = study_date
            
        if study_time != 'N/A' and len(study_time) >= 6:
            formatted_time = f"{study_time[:2]}:{study_time[2:4]}:{study_time[4:6]}"
        else:
            formatted_time = study_time
        
        # Get image dimensions
        if hasattr(dataset, 'pixel_array'):
            pixel_array = dataset.pixel_array
            dimensions = f"{pixel_array.shape[1]} × {pixel_array.shape[0]}"
        else:
            dimensions = "N/A"
        
        info = f"""<b>Patient Information:</b><br>
Name: {patient_name}<br>
ID: {patient_id}<br><br>
<b>Study Details:</b><br>
Date: {formatted_date}<br>
Time: {formatted_time}<br>
Modality: {modality}<br>
Institution: {institution}<br><br>
<b>Image Properties:</b><br>
Dimensions: {dimensions}<br>
Slice Position: {self.current_slice_index + 1} / {len(self.slices)}"""
        
        self.metadata_label.setText(info)
        self.slice_label.setText(f"Slice: {self.current_slice_index + 1} / {len(self.slices)}")
        
        # Update status bar
        self.status_bar.showMessage(f"Viewing slice {self.current_slice_index + 1} of {len(self.slices)} - {modality} study")

    def apply_window_level(self, image, level, width):
        min_val = level - width / 2
        max_val = level + width / 2
        
        slope = self.slices[self.current_slice_index].get("RescaleSlope", 1)
        intercept = self.slices[self.current_slice_index].get("RescaleIntercept", 0)
        image = image * slope + intercept

        windowed_image = np.clip(image, min_val, max_val)
        
        if max_val != min_val:
            normalized_image = ((windowed_image - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
        else:
            normalized_image = np.zeros_like(windowed_image, dtype=np.uint8)

        return normalized_image

    def handle_mouse_wl_adjust(self, level_change, width_change):
        if not self.slices: return
        
        new_level = self.level_slider.value() + level_change
        new_width = self.width_slider.value() + width_change

        new_level = max(self.level_slider.minimum(), min(new_level, self.level_slider.maximum()))
        new_width = max(self.width_slider.minimum(), min(new_width, self.width_slider.maximum()))

        # Set sliders without triggering signals repeatedly
        self.level_slider.blockSignals(True)
        self.width_slider.blockSignals(True)
        self.level_slider.setValue(new_level)
        self.width_slider.setValue(new_width)
        self.level_slider.blockSignals(False)
        self.width_slider.blockSignals(False)

        self.update_image() # Manually update since signals were blocked

    def apply_preset(self, preset):
        if not self.slices: return
        self.level_slider.setValue(preset["level"])
        self.width_slider.setValue(preset["width"])

    def update_image(self):
        if not self.slices: return

        current_slice_data = self.slices[self.current_slice_index].pixel_array.astype(np.float32)
        level = self.level_slider.value()
        width = self.width_slider.value()

        img_8bit = self.apply_window_level(current_slice_data, level, width)

        height, width_px = img_8bit.shape
        q_image = QImage(img_8bit.data, width_px, height, width_px, QImage.Format_Grayscale8)
        
        # Apply transformations
        transform = QTransform()
        
        # Apply rotation
        if self.rotation_angle != 0:
            transform.rotate(self.rotation_angle)
        
        # Apply flips
        if self.flip_horizontal_state:
            transform.scale(-1, 1)
        if self.flip_vertical_state:
            transform.scale(1, -1)
        
        pixmap = QPixmap.fromImage(q_image)
        if not transform.isIdentity():
            pixmap = pixmap.transformed(transform)
            
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        # Update window/level labels
        self.level_label.setText(f"Level: {level}")
        self.width_label.setText(f"Width: {width}")
        
    def resizeEvent(self, event):
        if self.pixmap_item.pixmap():
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    viewer = DicomViewer()
    viewer.show()
    sys.exit(app.exec_())
