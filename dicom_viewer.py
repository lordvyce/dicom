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
    QGraphicsPixmapItem, QFrame
)
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF

# --- Constants ---

STYLESHEET = """
QWidget {
    background-color: #2E2E2E;
    color: #E0E0E0;
    font-family: Arial, sans-serif;
}
QMainWindow {
    border: 1px solid #444;
}
QPushButton {
    background-color: #555555;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 5px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #6A6A6A;
}
QPushButton:pressed {
    background-color: #4A4A4A;
}
QLabel {
    font-size: 12px;
}
QSlider::groove:horizontal {
    border: 1px solid #444;
    height: 8px;
    background: #3A3A3A;
    margin: 2px 0;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #888888;
    border: 1px solid #999999;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}
QGraphicsView {
    border: 1px solid #444;
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
        self.setWindowTitle("DICOM Viewer v3.0")
        self.setGeometry(100, 100, 1200, 900)

        # Data
        self.slices = []
        self.current_slice_index = 0

        # UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left Panel (Controls)
        controls_layout = QVBoxLayout()
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        controls_widget.setMaximumWidth(300)

        # File Operations
        file_box = QVBoxLayout()
        self.btn_open_file = QPushButton("Open File")
        self.btn_open_file.clicked.connect(self.open_file)
        self.btn_open_folder = QPushButton("Open Folder (Series)")
        self.btn_open_folder.clicked.connect(self.open_folder)
        file_box.addWidget(self.btn_open_file)
        file_box.addWidget(self.btn_open_folder)
        controls_layout.addLayout(file_box)
        controls_layout.addWidget(self.create_separator())

        # Slice Navigation
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self.slice_slider_changed)
        self.slice_label = QLabel("Slice: N/A")
        controls_layout.addWidget(QLabel("Slice Navigation"))
        controls_layout.addWidget(self.slice_slider)
        controls_layout.addWidget(self.slice_label)
        controls_layout.addWidget(self.create_separator())

        # Window/Level Controls
        self.level_slider = QSlider(Qt.Horizontal)
        self.level_slider.setEnabled(False)
        self.level_slider.valueChanged.connect(self.update_image)
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setEnabled(False)
        self.width_slider.valueChanged.connect(self.update_image)
        controls_layout.addWidget(QLabel("Window Level (Brightness)"))
        controls_layout.addWidget(self.level_slider)
        controls_layout.addWidget(QLabel("Window Width (Contrast)"))
        controls_layout.addWidget(self.width_slider)
        controls_layout.addWidget(self.create_separator())

        # Window/Level Presets
        presets_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Window/Level Presets"))
        for name, values in PRESETS.items():
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, v=values: self.apply_preset(v))
            presets_layout.addWidget(btn)
        controls_layout.addLayout(presets_layout)
        controls_layout.addWidget(self.create_separator())

        # Metadata
        self.metadata_label = QLabel("Patient Info: N/A")
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setAlignment(Qt.AlignTop)
        controls_layout.addWidget(self.metadata_label)
        controls_layout.addStretch()

        # Right Panel (Image Display)
        self.scene = QGraphicsScene()
        self.view = DicomGraphicsView(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.view.windowLevelChanged.connect(self.handle_mouse_wl_adjust)

        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.view)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for slice navigation."""
        if not self.slices:
            return
        if event.key() == Qt.Key_Right:
            self.slice_slider.setValue(self.slice_slider.value() + 1)
        elif event.key() == Qt.Key_Left:
            self.slice_slider.setValue(self.slice_slider.value() - 1)

    # ... (All other methods like open_file, open_folder, load_dicom_series, etc. remain here) ...
    # Note: These methods are largely unchanged from v2, but are included below for completeness.
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open DICOM File", "", "DICOM Files (*.dcm; *.dicom)")
        if file_path:
            self.load_dicom_series([file_path])

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open DICOM Folder")
        if folder_path:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
            dicom_files = [f for f in files if f.lower().endswith(('.dcm', '.dicom')) or not '.' in os.path.basename(f)]
            
            if dicom_files:
                self.load_dicom_series(dicom_files)
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
        
        self.level_slider.setEnabled(True)
        self.width_slider.setEnabled(True)

    def slice_slider_changed(self, value):
        self.current_slice_index = value
        self.update_metadata()
        self.update_image()

    def update_metadata(self):
        if not self.slices: return
        dataset = self.slices[self.current_slice_index]
        info = (
            f"Patient Name: {dataset.get('PatientName', 'N/A')}\n"
            f"Study Date: {dataset.get('StudyDate', 'N/A')}\n"
            f"Modality: {dataset.get('Modality', 'N/A')}\n"
        )
        self.metadata_label.setText(info)
        self.slice_label.setText(f"Slice: {self.current_slice_index + 1} / {len(self.slices)}")

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

        height, width = img_8bit.shape
        q_image = QImage(img_8bit.data, width, height, width, QImage.Format_Grayscale8)
        
        pixmap = QPixmap.fromImage(q_image)
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
    def resizeEvent(self, event):
        if self.pixmap_item.pixmap():
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    viewer = DicomViewer()
    viewer.show()
    sys.exit(app.exec_())
