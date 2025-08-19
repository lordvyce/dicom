"""
Enhanced Main Window - Professional DICOM viewer with advanced features
"""
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFileDialog, QLabel, QSlider, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QFrame, QSplitter, QGroupBox, QStatusBar,
    QMenuBar, QAction, QToolBar, QDockWidget, QTextEdit, QComboBox,
    QCheckBox, QSpinBox, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QKeySequence, QIcon, QFont
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF, QPointF, QTimer
import numpy as np

from core.dicom_handler import DicomHandler
from core.image_processor import ImageProcessor
from core.measurement_tools import MeasurementManager, MeasurementMode
from ui.metadata_browser import MetadataBrowser


# Window/Level presets
PRESETS = {
    "Soft Tissue": {"level": 40, "width": 400},
    "Lung": {"level": -600, "width": 1500},
    "Bone": {"level": 500, "width": 2000},
    "Brain": {"level": 40, "width": 80},
    "Liver": {"level": 50, "width": 150},
}


class EnhancedDicomView(QGraphicsView):
    """Enhanced graphics view with measurement support."""
    
    windowLevelChanged = pyqtSignal(int, int)
    pixelValueRequested = pyqtSignal(QPointF)
    measurementClicked = pyqtSignal(QPointF)
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self._is_adjusting_wl = False
        self._last_mouse_pos = QPoint()
        self.measurement_mode_active = False
        
    def wheelEvent(self, event):
        """Zoom in or out with the mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event):
        """Handle mouse press for window/level or measurements."""
        scene_pos = self.mapToScene(event.pos())
        
        if event.button() == Qt.LeftButton:
            if self.measurement_mode_active:
                self.measurementClicked.emit(scene_pos)
            else:
                self._is_adjusting_wl = True
                self._last_mouse_pos = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for window/level adjustment or pixel values."""
        scene_pos = self.mapToScene(event.pos())
        self.pixelValueRequested.emit(scene_pos)
        
        if self._is_adjusting_wl and not self.measurement_mode_active:
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
    
    def set_measurement_mode(self, active: bool):
        """Enable/disable measurement mode."""
        self.measurement_mode_active = active
        if active:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)


class MainWindow(QMainWindow):
    """Enhanced main window with professional features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced DICOM Viewer v4.0")
        self.setGeometry(100, 100, 1400, 1000)
        
        # Core components
        self.dicom_handler = DicomHandler()
        self.image_processor = ImageProcessor()
        
        # UI setup
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbars()
        self.setup_status_bar()
        self.setup_shortcuts()
        
        # Measurement tools
        self.measurement_manager = MeasurementManager(self.scene)
        
        # Status
        self.pixel_value_label = QLabel("Pixel: N/A")
        self.hu_value_label = QLabel("HU: N/A")
        self.measurement_status_label = QLabel("")
        
    def setup_ui(self):
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter for resizable panes
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # Left panel with controls
        self.setup_left_panel(main_splitter)
        
        # Center panel with image viewer
        self.setup_center_panel(main_splitter)
        
        # Right panel with metadata
        self.setup_right_panel(main_splitter)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 600, 400])
    
    def setup_left_panel(self, parent_splitter):
        """Set up left control panel."""
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.btn_open_file = QPushButton("Open File")
        self.btn_open_file.clicked.connect(self.open_file)
        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.clicked.connect(self.open_folder)
        
        file_layout.addWidget(self.btn_open_file)
        file_layout.addWidget(self.btn_open_folder)
        layout.addWidget(file_group)
        
        # Navigation controls
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self.slice_changed)
        self.slice_label = QLabel("Slice: N/A")
        
        nav_layout.addWidget(QLabel("Slice:"))
        nav_layout.addWidget(self.slice_slider)
        nav_layout.addWidget(self.slice_label)
        layout.addWidget(nav_group)
        
        # Window/Level controls
        wl_group = QGroupBox("Window/Level")
        wl_layout = QVBoxLayout(wl_group)
        
        self.level_slider = QSlider(Qt.Horizontal)
        self.level_slider.setEnabled(False)
        self.level_slider.valueChanged.connect(self.update_image)
        self.level_label = QLabel("Level: 0")
        
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setEnabled(False)
        self.width_slider.valueChanged.connect(self.update_image)
        self.width_label = QLabel("Width: 0")
        
        wl_layout.addWidget(QLabel("Level (Brightness):"))
        wl_layout.addWidget(self.level_slider)
        wl_layout.addWidget(self.level_label)
        wl_layout.addWidget(QLabel("Width (Contrast):"))
        wl_layout.addWidget(self.width_slider)
        wl_layout.addWidget(self.width_label)
        
        # Presets
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom"] + list(PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(QLabel("Preset:"))
        preset_layout.addWidget(self.preset_combo)
        wl_layout.addLayout(preset_layout)
        
        layout.addWidget(wl_group)
        
        # Measurement tools
        measure_group = QGroupBox("Measurement Tools")
        measure_layout = QVBoxLayout(measure_group)
        
        self.btn_crosshair = QPushButton("Crosshair")
        self.btn_crosshair.setCheckable(True)
        self.btn_crosshair.clicked.connect(lambda: self.set_measurement_mode(MeasurementMode.CROSSHAIR))
        
        self.btn_distance = QPushButton("Distance")
        self.btn_distance.setCheckable(True)
        self.btn_distance.clicked.connect(lambda: self.set_measurement_mode(MeasurementMode.DISTANCE))
        
        self.btn_angle = QPushButton("Angle")
        self.btn_angle.setCheckable(True)
        self.btn_angle.clicked.connect(lambda: self.set_measurement_mode(MeasurementMode.ANGLE))
        
        self.btn_clear_measurements = QPushButton("Clear All")
        self.btn_clear_measurements.clicked.connect(self.clear_measurements)
        
        measure_layout.addWidget(self.btn_crosshair)
        measure_layout.addWidget(self.btn_distance)
        measure_layout.addWidget(self.btn_angle)
        measure_layout.addWidget(self.btn_clear_measurements)
        
        layout.addWidget(measure_group)
        
        # Export options
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.btn_export_image = QPushButton("Export Image")
        self.btn_export_image.clicked.connect(self.export_image)
        
        export_layout.addWidget(self.btn_export_image)
        layout.addWidget(export_group)
        
        layout.addStretch()
        parent_splitter.addWidget(left_panel)
    
    def setup_center_panel(self, parent_splitter):
        """Set up center image viewing panel."""
        center_panel = QWidget()
        layout = QVBoxLayout(center_panel)
        
        # Image viewer
        self.scene = QGraphicsScene()
        self.view = EnhancedDicomView(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        # Connect signals
        self.view.windowLevelChanged.connect(self.handle_mouse_wl_adjust)
        self.view.pixelValueRequested.connect(self.update_pixel_info)
        self.view.measurementClicked.connect(self.handle_measurement_click)
        
        layout.addWidget(self.view)
        parent_splitter.addWidget(center_panel)
    
    def setup_right_panel(self, parent_splitter):
        """Set up right metadata panel."""
        # Create dockable metadata browser
        self.metadata_dock = QDockWidget("Metadata", self)
        self.metadata_browser = MetadataBrowser()
        self.metadata_dock.setWidget(self.metadata_browser)
        self.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
    
    def setup_menus(self):
        """Set up menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_file_action = QAction('Open File...', self)
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        open_folder_action = QAction('Open Folder...', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('Export Image...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_image)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        fit_action = QAction('Fit to Window', self)
        fit_action.setShortcut('Ctrl+0')
        fit_action.triggered.connect(self.fit_to_window)
        view_menu.addAction(fit_action)
        
        actual_size_action = QAction('Actual Size', self)
        actual_size_action.setShortcut('Ctrl+1')
        actual_size_action.triggered.connect(self.actual_size)
        view_menu.addAction(actual_size_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        clear_measurements_action = QAction('Clear Measurements', self)
        clear_measurements_action.setShortcut('Ctrl+K')
        clear_measurements_action.triggered.connect(self.clear_measurements)
        tools_menu.addAction(clear_measurements_action)
    
    def setup_toolbars(self):
        """Set up toolbars."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add common actions to toolbar
        toolbar.addAction("Open", self.open_file)
        toolbar.addSeparator()
        toolbar.addAction("Fit", self.fit_to_window)
        toolbar.addAction("1:1", self.actual_size)
        toolbar.addSeparator()
        toolbar.addAction("Export", self.export_image)
    
    def setup_status_bar(self):
        """Set up status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Add permanent widgets
        status_bar.addPermanentWidget(self.pixel_value_label)
        status_bar.addPermanentWidget(self.hu_value_label)
        status_bar.addWidget(self.measurement_status_label)
        
        status_bar.showMessage("Ready")
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Navigation shortcuts are handled in keyPressEvent
        pass
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if not self.dicom_handler.slices:
            return
            
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
            current = self.slice_slider.value()
            self.slice_slider.setValue(min(current + 1, self.slice_slider.maximum()))
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
            current = self.slice_slider.value()
            self.slice_slider.setValue(max(current - 1, self.slice_slider.minimum()))
        elif event.key() == Qt.Key_Home:
            self.slice_slider.setValue(0)
        elif event.key() == Qt.Key_End:
            self.slice_slider.setValue(self.slice_slider.maximum())
    
    def open_file(self):
        """Open a single DICOM file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DICOM File", "", 
            "DICOM Files (*.dcm *.dicom);;All Files (*)"
        )
        if file_path:
            if self.dicom_handler.load_dicom_series([file_path]):
                self.setup_ui_for_loaded_data()
                self.statusBar().showMessage(f"Loaded: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load DICOM file.")
    
    def open_folder(self):
        """Open a folder containing DICOM files."""
        folder_path = QFileDialog.getExistingDirectory(self, "Open DICOM Folder")
        if folder_path:
            if self.dicom_handler.load_dicom_folder(folder_path):
                self.setup_ui_for_loaded_data()
                self.statusBar().showMessage(f"Loaded series from: {os.path.basename(folder_path)}")
            else:
                QMessageBox.warning(self, "Error", "No valid DICOM files found in folder.")
    
    def setup_ui_for_loaded_data(self):
        """Configure UI after loading DICOM data."""
        slice_count = self.dicom_handler.get_slice_count()
        
        # Setup slice navigation
        if slice_count > 1:
            self.slice_slider.setEnabled(True)
            self.slice_slider.setRange(0, slice_count - 1)
            self.slice_slider.setValue(self.dicom_handler.current_slice_index)
        else:
            self.slice_slider.setEnabled(False)
        
        # Setup window/level controls
        level, width = self.dicom_handler.get_window_level_defaults()
        pixel_data = self.dicom_handler.get_pixel_data()
        
        if pixel_data is not None:
            data_min, data_max = pixel_data.min(), pixel_data.max()
            
            self.level_slider.setRange(int(data_min), int(data_max))
            self.width_slider.setRange(1, int(data_max - data_min))
            
            self.level_slider.setValue(int(level))
            self.width_slider.setValue(int(width))
            
            self.level_slider.setEnabled(True)
            self.width_slider.setEnabled(True)
        
        # Update displays
        self.update_slice_info()
        self.update_metadata()
        self.update_image()
        self.fit_to_window()
    
    def slice_changed(self, value):
        """Handle slice navigation."""
        if self.dicom_handler.set_current_slice(value):
            self.update_slice_info()
            self.update_metadata()
            self.update_image()
    
    def update_slice_info(self):
        """Update slice information display."""
        if self.dicom_handler.slices:
            current = self.dicom_handler.current_slice_index + 1
            total = self.dicom_handler.get_slice_count()
            self.slice_label.setText(f"Slice: {current} / {total}")
        else:
            self.slice_label.setText("Slice: N/A")
    
    def update_metadata(self):
        """Update metadata browser."""
        current_slice = self.dicom_handler.get_current_slice()
        if current_slice:
            self.metadata_browser.update_metadata(
                current_slice,
                self.dicom_handler.current_slice_index,
                self.dicom_handler.get_slice_count()
            )
    
    def update_image(self):
        """Update the displayed image."""
        pixel_data = self.dicom_handler.get_pixel_data()
        if pixel_data is None:
            return
        
        current_slice = self.dicom_handler.get_current_slice()
        if current_slice is None:
            return
        
        # Get window/level values
        level = self.level_slider.value()
        width = self.width_slider.value()
        
        # Update labels
        self.level_label.setText(f"Level: {level}")
        self.width_label.setText(f"Width: {width}")
        
        # Get rescale parameters
        slope = current_slice.get("RescaleSlope", 1.0)
        intercept = current_slice.get("RescaleIntercept", 0.0)
        
        # Process image
        img_8bit = self.image_processor.apply_window_level(
            pixel_data, level, width, slope, intercept
        )
        
        # Convert to QImage and display
        qimage = self.image_processor.array_to_qimage(img_8bit)
        pixmap = self.image_processor.qimage_to_pixmap(qimage)
        
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
    
    def handle_mouse_wl_adjust(self, level_change, width_change):
        """Handle mouse-based window/level adjustment."""
        if not self.dicom_handler.slices:
            return
        
        new_level = self.level_slider.value() + level_change
        new_width = self.width_slider.value() + width_change
        
        # Clamp values to slider ranges
        new_level = max(self.level_slider.minimum(), 
                       min(new_level, self.level_slider.maximum()))
        new_width = max(self.width_slider.minimum(), 
                       min(new_width, self.width_slider.maximum()))
        
        # Update sliders without triggering signals
        self.level_slider.blockSignals(True)
        self.width_slider.blockSignals(True)
        self.level_slider.setValue(new_level)
        self.width_slider.setValue(new_width)
        self.level_slider.blockSignals(False)
        self.width_slider.blockSignals(False)
        
        # Update display
        self.update_image()
        
        # Reset preset combo
        self.preset_combo.setCurrentText("Custom")
    
    def apply_preset(self, preset_name):
        """Apply window/level preset."""
        if preset_name == "Custom" or preset_name not in PRESETS:
            return
        
        preset = PRESETS[preset_name]
        self.level_slider.setValue(preset["level"])
        self.width_slider.setValue(preset["width"])
    
    def update_pixel_info(self, scene_pos):
        """Update pixel value information."""
        pixel_data = self.dicom_handler.get_pixel_data()
        current_slice = self.dicom_handler.get_current_slice()
        
        if pixel_data is None or current_slice is None:
            return
        
        x, y = int(scene_pos.x()), int(scene_pos.y())
        
        if 0 <= x < pixel_data.shape[1] and 0 <= y < pixel_data.shape[0]:
            raw_value = pixel_data[y, x]
            self.pixel_value_label.setText(f"Pixel: {raw_value:.0f}")
            
            # Calculate HU value
            slope = current_slice.get("RescaleSlope", 1.0)
            intercept = current_slice.get("RescaleIntercept", 0.0)
            hu_value = raw_value * slope + intercept
            self.hu_value_label.setText(f"HU: {hu_value:.0f}")
            
            # Update crosshair position
            self.measurement_manager.update_crosshair_position(scene_pos)
        else:
            self.pixel_value_label.setText("Pixel: N/A")
            self.hu_value_label.setText("HU: N/A")
    
    def set_measurement_mode(self, mode):
        """Set measurement mode."""
        # Reset all measurement buttons
        self.btn_crosshair.setChecked(False)
        self.btn_distance.setChecked(False)
        self.btn_angle.setChecked(False)
        
        # Set active button
        if mode == MeasurementMode.CROSSHAIR:
            self.btn_crosshair.setChecked(True)
        elif mode == MeasurementMode.DISTANCE:
            self.btn_distance.setChecked(True)
        elif mode == MeasurementMode.ANGLE:
            self.btn_angle.setChecked(True)
        
        # Update measurement manager and view
        self.measurement_manager.set_measurement_mode(mode)
        self.view.set_measurement_mode(mode != MeasurementMode.NONE)
        
        # Update status
        mode_names = {
            MeasurementMode.NONE: "Normal viewing mode",
            MeasurementMode.CROSSHAIR: "Crosshair mode - move mouse to see pixel values",
            MeasurementMode.DISTANCE: "Distance measurement - click two points",
            MeasurementMode.ANGLE: "Angle measurement - click three points"
        }
        self.measurement_status_label.setText(mode_names.get(mode, ""))
    
    def handle_measurement_click(self, scene_pos):
        """Handle measurement tool clicks."""
        pixel_spacing = self.dicom_handler.get_pixel_spacing()
        status = self.measurement_manager.handle_click(scene_pos, pixel_spacing)
        
        if status:
            self.measurement_status_label.setText(status)
            # Auto-reset to crosshair mode after completing a measurement
            if ":" in status:  # Completed measurement (contains result)
                QTimer.singleShot(2000, lambda: self.set_measurement_mode(MeasurementMode.CROSSHAIR))
    
    def clear_measurements(self):
        """Clear all measurements."""
        self.measurement_manager.clear_measurements()
        self.measurement_status_label.setText("Measurements cleared")
        QTimer.singleShot(2000, lambda: self.measurement_status_label.setText(""))
    
    def export_image(self):
        """Export current image."""
        if not self.dicom_handler.slices:
            QMessageBox.warning(self, "Warning", "No image to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Image", "", 
            "PNG Files (*.png);;JPEG Files (*.jpg);;TIFF Files (*.tiff)"
        )
        
        if file_path:
            # Get current pixmap
            pixmap = self.pixmap_item.pixmap()
            if pixmap and not pixmap.isNull():
                success = pixmap.save(file_path)
                if success:
                    self.statusBar().showMessage(f"Exported: {os.path.basename(file_path)}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export image.")
    
    def fit_to_window(self):
        """Fit image to window."""
        if self.pixmap_item.pixmap():
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
    
    def actual_size(self):
        """Show image at actual size."""
        if self.pixmap_item.pixmap():
            self.view.resetTransform()
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        # Auto-fit on resize if image is loaded
        if hasattr(self, 'pixmap_item') and self.pixmap_item.pixmap():
            QTimer.singleShot(100, self.fit_to_window)  # Delay to ensure resize is complete