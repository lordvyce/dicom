#!/usr/bin/env python3
"""
Enhanced DICOM Viewer v4.0 - Production-Grade Medical Imaging Application

This is a comprehensive upgrade from the basic DICOM viewer, featuring:
- Modular architecture for maintainability and extensibility
- Enhanced measurement tools (distance, angle, crosshair with pixel values)
- Professional metadata browser with full DICOM tag display
- Advanced image processing and window/level controls
- Export functionality and keyboard shortcuts
- Dockable panels and professional UI
- Real-world measurement capabilities with pixel spacing
- Hounsfield Unit (HU) value display for CT images

New Features in v4.0:
- Crosshair cursor with real-time pixel value and HU display
- Distance measurement with calibrated pixel spacing
- Angle measurement tool
- Comprehensive metadata browser with searchable tags
- Enhanced UI with dockable panels and toolbars
- Keyboard shortcuts for efficient navigation
- Export functionality (PNG, JPEG, TIFF)
- Professional status bar with measurement feedback
- Modular code structure for easy extension

Dependencies:
pip install PyQt5 pydicom numpy pylibjpeg pylibjpeg-libjpeg

Usage:
python main.py [dicom_file_or_folder]
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add current directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


# Professional dark theme stylesheet
DARK_THEME = """
QWidget {
    background-color: #2E2E2E;
    color: #E0E0E0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
}

QMainWindow {
    border: 1px solid #444;
}

QPushButton {
    background-color: #555555;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 80px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #6A6A6A;
    border-color: #888888;
}

QPushButton:pressed {
    background-color: #4A4A4A;
    border-color: #333333;
}

QPushButton:checked {
    background-color: #0078D4;
    border-color: #106EBE;
    color: white;
}

QPushButton:disabled {
    background-color: #3A3A3A;
    border-color: #444444;
    color: #777777;
}

QLabel {
    font-size: 9pt;
    color: #E0E0E0;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #555555;
    border-radius: 5px;
    margin-top: 1ex;
    padding-top: 5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #CCCCCC;
}

QSlider::groove:horizontal {
    border: 1px solid #444;
    height: 8px;
    background: #3A3A3A;
    margin: 2px 0;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #0078D4;
    border: 1px solid #106EBE;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #1084D8;
}

QGraphicsView {
    border: 1px solid #555555;
    background-color: #1E1E1E;
}

QComboBox {
    background-color: #555555;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #888888;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #E0E0E0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #555555;
    border: 1px solid #666666;
    selection-background-color: #0078D4;
}

QTreeWidget {
    background-color: #1E1E1E;
    border: 1px solid #555555;
    alternate-background-color: #2A2A2A;
}

QTreeWidget::item {
    padding: 2px;
    border-bottom: 1px solid #333333;
}

QTreeWidget::item:selected {
    background-color: #0078D4;
}

QTreeWidget::item:hover {
    background-color: #404040;
}

QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #555555;
    selection-background-color: #0078D4;
}

QLineEdit {
    background-color: #555555;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 20px;
}

QLineEdit:focus {
    border-color: #0078D4;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2E2E2E;
}

QTabBar::tab {
    background-color: #555555;
    border: 1px solid #666666;
    padding: 6px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0078D4;
    border-color: #106EBE;
}

QTabBar::tab:hover {
    background-color: #6A6A6A;
}

QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #555555;
    color: #E0E0E0;
    padding: 4px;
    border: 1px solid #666666;
}

QMenuBar {
    background-color: #555555;
    border-bottom: 1px solid #666666;
}

QMenuBar::item {
    padding: 4px 8px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #6A6A6A;
}

QMenu {
    background-color: #555555;
    border: 1px solid #666666;
}

QMenu::item {
    padding: 6px 20px;
}

QMenu::item:selected {
    background-color: #0078D4;
}

QToolBar {
    background-color: #555555;
    border: 1px solid #666666;
    spacing: 2px;
}

QToolBar::separator {
    background-color: #666666;
    width: 1px;
    height: 20px;
    margin: 0 4px;
}

QStatusBar {
    background-color: #555555;
    border-top: 1px solid #666666;
    color: #E0E0E0;
}

QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QScrollBar:vertical {
    background-color: #3A3A3A;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #666666;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #888888;
}

QScrollBar:horizontal {
    background-color: #3A3A3A;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #666666;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #888888;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}
"""


def setup_application():
    """Set up the QApplication with proper settings."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced DICOM Viewer")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("Medical Imaging Solutions")
    
    # Apply dark theme
    app.setStyleSheet(DARK_THEME)
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app


def main():
    """Main application entry point."""
    app = setup_application()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            # Load single file
            if window.dicom_handler.load_dicom_series([path]):
                window.setup_ui_for_loaded_data()
                window.statusBar().showMessage(f"Loaded: {os.path.basename(path)}")
        elif os.path.isdir(path):
            # Load folder
            if window.dicom_handler.load_dicom_folder(path):
                window.setup_ui_for_loaded_data()
                window.statusBar().showMessage(f"Loaded series from: {os.path.basename(path)}")
    
    # Start event loop
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())