# Enhanced DICOM Viewer v4.0

A professional-grade DICOM viewer application with advanced measurement tools, comprehensive metadata browsing, and production-ready features for medical imaging workflows.

## 🚀 New Features in v4.0

### Enhanced Measurement Tools
- **Crosshair Cursor**: Real-time pixel value and Hounsfield Unit (HU) display
- **Distance Measurement**: Calibrated measurements using DICOM pixel spacing
- **Angle Measurement**: Three-point angle measurement tool
- **Interactive Annotations**: Persistent measurement overlays

### Professional Metadata Browser
- **Comprehensive Tag Display**: Full DICOM tag tree with search functionality
- **Patient Information**: Organized demographics and study details
- **Summary View**: Key imaging parameters at a glance
- **Searchable Tags**: Quick filtering of DICOM elements

### Advanced UI Features
- **Dockable Panels**: Flexible workspace organization
- **Professional Theme**: Dark mode optimized for medical imaging
- **Keyboard Shortcuts**: Efficient navigation and control
- **Status Bar**: Real-time feedback and measurement results
- **Toolbars**: Quick access to common functions

### Export and Integration
- **Multiple Formats**: Export to PNG, JPEG, TIFF with annotations
- **Measurement Preservation**: Measurements included in exported images
- **Command Line Support**: Batch processing capabilities

## 📋 Requirements

- Python 3.7+
- PyQt5
- pydicom
- numpy
- pylibjpeg
- pylibjpeg-libjpeg

## 🛠️ Installation

```bash
pip install PyQt5 pydicom numpy pylibjpeg pylibjpeg-libjpeg
```

## 🎯 Usage

### Basic Usage
```bash
# Launch the application
python main.py

# Open a specific DICOM file
python main.py /path/to/dicom/file.dcm

# Open a folder containing DICOM series
python main.py /path/to/dicom/folder/
```

### Keyboard Shortcuts
- `Ctrl+O`: Open file
- `Ctrl+Shift+O`: Open folder
- `Ctrl+E`: Export image
- `Ctrl+0`: Fit to window
- `Ctrl+1`: Actual size
- `Ctrl+K`: Clear measurements
- `Arrow Keys`: Navigate slices
- `Home/End`: First/last slice

### Measurement Tools
1. **Crosshair Mode**: Move mouse to see pixel values and HU
2. **Distance Mode**: Click two points to measure distance
3. **Angle Mode**: Click three points (first, vertex, third) to measure angle

### Window/Level Presets
- Soft Tissue: Level 40, Width 400
- Lung: Level -600, Width 1500
- Bone: Level 500, Width 2000
- Brain: Level 40, Width 80
- Liver: Level 50, Width 150

## 🏗️ Architecture

### Modular Structure
```
├── main.py                 # Application entry point
├── core/                   # Core functionality
│   ├── dicom_handler.py    # DICOM file loading and management
│   ├── image_processor.py  # Image processing and window/level
│   └── measurement_tools.py # Interactive measurement tools
├── ui/                     # User interface components
│   ├── main_window.py      # Main application window
│   └── metadata_browser.py # Enhanced metadata display
├── utils/                  # Utility modules
│   └── settings_manager.py # Application settings
├── rendering/              # Future 3D rendering capabilities
└── networking/             # Future PACS integration
```

### Core Components

#### DicomHandler
- Multi-file and series loading
- Intelligent slice sorting
- Pixel spacing extraction
- Window/level defaults

#### ImageProcessor
- Window/level transformations
- Hounsfield Unit calculations
- Distance and angle calculations
- Image format conversions

#### MeasurementManager
- Interactive measurement tools
- Annotation persistence
- Crosshair positioning
- Real-time feedback

#### MetadataBrowser
- Complete DICOM tag display
- Searchable tag tree
- Patient information summary
- Multi-tab organization

## 🎨 Features in Detail

### Real-World Measurements
The viewer uses DICOM pixel spacing information to provide accurate real-world measurements:
- Distance measurements in millimeters
- Calibrated to actual image resolution
- Supports different pixel spacing in X and Y directions

### Hounsfield Unit Display
For CT images, the viewer displays Hounsfield Units (HU) using:
- RescaleSlope and RescaleIntercept from DICOM headers
- Real-time HU values as mouse moves over image
- Critical for CT image analysis

### Professional Workflow
- Persistent measurement annotations
- Export with measurements preserved
- Professional dark theme optimized for medical imaging
- Dockable panels for customizable workspace

## 🔧 Customization

### Settings
The application stores settings in:
- Windows: `%APPDATA%/enhanced_dicom_viewer/settings.json`
- Unix/Linux: `~/.config/enhanced_dicom_viewer/settings.json`

Configurable options include:
- Window sizes and positions
- Default presets
- Measurement preferences
- Export settings
- UI theme options

### Extending Functionality
The modular architecture makes it easy to add new features:
- Add new measurement tools in `core/measurement_tools.py`
- Extend image processing in `core/image_processor.py`
- Add UI components in the `ui/` directory
- Implement 3D rendering in `rendering/`
- Add PACS connectivity in `networking/`

## 📝 Development Notes

### Code Quality
- Type hints throughout codebase
- Comprehensive error handling
- Modular, testable design
- Professional naming conventions

### Performance Optimizations
- Efficient image processing
- Memory-conscious operations
- Responsive UI updates
- Background processing ready

### Future Enhancements
- Multi-planar reconstruction (MPR)
- 3D volume rendering
- PACS integration (C-STORE, C-FIND)
- DICOM SR support
- Advanced export options
- Anonymization tools

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Display Issues**: Verify PyQt5 installation and display drivers
3. **File Loading**: Check DICOM file format and permissions
4. **Measurements**: Verify pixel spacing is available in DICOM headers

### Support
For issues or feature requests, check the code comments and modular structure for guidance on extending functionality.

## 📄 License

This is an educational and professional development project. Please ensure compliance with medical device regulations if used in clinical environments.

## 🔄 Changelog

### v4.0 (Current)
- ✅ Modular architecture implementation
- ✅ Enhanced measurement tools (crosshair, distance, angle)
- ✅ Professional metadata browser with search
- ✅ Advanced UI with dockable panels
- ✅ Export functionality with multiple formats
- ✅ Keyboard shortcuts and professional workflows
- ✅ Settings management system
- ✅ Real-world measurements with pixel spacing
- ✅ Hounsfield Unit display for CT images

### v3.0 (Previous)
- Basic QGraphicsView implementation
- Window/level presets
- Dark theme
- Keyboard navigation