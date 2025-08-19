"""
Enhanced Metadata Browser - Comprehensive DICOM tag display and editing
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                            QTreeWidgetItem, QLabel, QPushButton, QLineEdit,
                            QTextEdit, QTabWidget, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import pydicom
from typing import Optional


class MetadataBrowser(QWidget):
    """Enhanced metadata browser with full DICOM tag display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_dataset: Optional[pydicom.Dataset] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Summary tab
        self.setup_summary_tab()
        
        # Full tags tab
        self.setup_full_tags_tab()
        
        # Patient info tab  
        self.setup_patient_tab()
    
    def setup_summary_tab(self):
        """Set up summary information tab."""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        # Key information display
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        font = QFont("Courier", 9)
        self.summary_text.setFont(font)
        layout.addWidget(QLabel("Key Information:"))
        layout.addWidget(self.summary_text)
        
        # Slice information
        slice_group = QGroupBox("Slice Information")
        slice_layout = QVBoxLayout(slice_group)
        
        self.slice_info_label = QLabel("No slice loaded")
        slice_layout.addWidget(self.slice_info_label)
        
        layout.addWidget(slice_group)
        layout.addStretch()
        
        self.tab_widget.addTab(summary_widget, "Summary")
    
    def setup_full_tags_tab(self):
        """Set up full DICOM tags display."""
        tags_widget = QWidget()
        layout = QVBoxLayout(tags_widget)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_tags)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Tags tree
        self.tags_tree = QTreeWidget()
        self.tags_tree.setHeaderLabels(["Tag", "Name", "VR", "Value"])
        self.tags_tree.setColumnWidth(0, 100)
        self.tags_tree.setColumnWidth(1, 200)
        self.tags_tree.setColumnWidth(2, 50)
        
        font = QFont("Courier", 8)
        self.tags_tree.setFont(font)
        
        layout.addWidget(self.tags_tree)
        
        self.tab_widget.addTab(tags_widget, "All Tags")
    
    def setup_patient_tab(self):
        """Set up patient information tab."""
        patient_widget = QWidget()
        layout = QVBoxLayout(patient_widget)
        
        # Patient demographics
        demo_group = QGroupBox("Patient Demographics")
        demo_layout = QVBoxLayout(demo_group)
        
        self.patient_name_label = QLabel("Name: N/A")
        self.patient_id_label = QLabel("ID: N/A")
        self.patient_sex_label = QLabel("Sex: N/A")
        self.patient_age_label = QLabel("Age: N/A")
        self.patient_dob_label = QLabel("DOB: N/A")
        
        demo_layout.addWidget(self.patient_name_label)
        demo_layout.addWidget(self.patient_id_label)
        demo_layout.addWidget(self.patient_sex_label)
        demo_layout.addWidget(self.patient_age_label)
        demo_layout.addWidget(self.patient_dob_label)
        
        layout.addWidget(demo_group)
        
        # Study information
        study_group = QGroupBox("Study Information")
        study_layout = QVBoxLayout(study_group)
        
        self.study_date_label = QLabel("Date: N/A")
        self.study_time_label = QLabel("Time: N/A")
        self.study_desc_label = QLabel("Description: N/A")
        self.modality_label = QLabel("Modality: N/A")
        self.institution_label = QLabel("Institution: N/A")
        
        study_layout.addWidget(self.study_date_label)
        study_layout.addWidget(self.study_time_label)
        study_layout.addWidget(self.study_desc_label)
        study_layout.addWidget(self.modality_label)
        study_layout.addWidget(self.institution_label)
        
        layout.addWidget(study_group)
        
        # Series information
        series_group = QGroupBox("Series Information")
        series_layout = QVBoxLayout(series_group)
        
        self.series_date_label = QLabel("Date: N/A")
        self.series_time_label = QLabel("Time: N/A")
        self.series_desc_label = QLabel("Description: N/A")
        self.series_number_label = QLabel("Number: N/A")
        
        series_layout.addWidget(self.series_date_label)
        series_layout.addWidget(self.series_time_label)
        series_layout.addWidget(self.series_desc_label)
        series_layout.addWidget(self.series_number_label)
        
        layout.addWidget(series_group)
        layout.addStretch()
        
        self.tab_widget.addTab(patient_widget, "Patient Info")
    
    def update_metadata(self, dataset: pydicom.Dataset, slice_index: int, total_slices: int):
        """
        Update all metadata displays with new dataset.
        
        Args:
            dataset: DICOM dataset to display
            slice_index: Current slice index (0-based)
            total_slices: Total number of slices
        """
        self.current_dataset = dataset
        
        # Update summary
        self.update_summary(dataset, slice_index, total_slices)
        
        # Update full tags
        self.update_full_tags(dataset)
        
        # Update patient info
        self.update_patient_info(dataset)
    
    def update_summary(self, dataset: pydicom.Dataset, slice_index: int, total_slices: int):
        """Update summary tab."""
        summary_text = []
        
        # Basic info
        summary_text.append(f"Patient: {dataset.get('PatientName', 'N/A')}")
        summary_text.append(f"Study Date: {dataset.get('StudyDate', 'N/A')}")
        summary_text.append(f"Modality: {dataset.get('Modality', 'N/A')}")
        summary_text.append(f"Slice: {slice_index + 1} / {total_slices}")
        summary_text.append("")
        
        # Image properties
        if hasattr(dataset, 'pixel_array'):
            shape = dataset.pixel_array.shape
            summary_text.append(f"Image Size: {shape[1]} x {shape[0]}")
        
        if 'PixelSpacing' in dataset:
            spacing = dataset.PixelSpacing
            summary_text.append(f"Pixel Spacing: {spacing[0]:.3f} x {spacing[1]:.3f} mm")
        
        if 'SliceThickness' in dataset:
            summary_text.append(f"Slice Thickness: {dataset.SliceThickness} mm")
        
        # Window/Level
        if 'WindowCenter' in dataset:
            wc = dataset.WindowCenter
            if isinstance(wc, list):
                wc = wc[0]
            summary_text.append(f"Window Center: {wc}")
        
        if 'WindowWidth' in dataset:
            ww = dataset.WindowWidth
            if isinstance(ww, list):
                ww = ww[0]
            summary_text.append(f"Window Width: {ww}")
        
        self.summary_text.setPlainText("\\n".join(summary_text))
        
        # Update slice info
        slice_info = f"Slice {slice_index + 1} of {total_slices}"
        if 'InstanceNumber' in dataset:
            slice_info += f" (Instance: {dataset.InstanceNumber})"
        self.slice_info_label.setText(slice_info)
    
    def update_full_tags(self, dataset: pydicom.Dataset):
        """Update full tags tree."""
        self.tags_tree.clear()
        
        # Recursively add all tags
        self._add_dataset_to_tree(dataset, self.tags_tree.invisibleRootItem())
        
        # Expand first level
        for i in range(self.tags_tree.topLevelItemCount()):
            item = self.tags_tree.topLevelItem(i)
            if item.childCount() > 0:
                item.setExpanded(False)  # Keep collapsed for performance
    
    def _add_dataset_to_tree(self, dataset: pydicom.Dataset, parent_item: QTreeWidgetItem):
        """Recursively add dataset elements to tree."""
        for elem in dataset:
            try:
                tag_str = f"({elem.tag.group:04X},{elem.tag.element:04X})"
                name = elem.name
                vr = elem.VR
                
                # Format value
                if elem.VR == 'SQ':  # Sequence
                    value = f"Sequence ({len(elem.value)} items)"
                elif len(str(elem.value)) > 100:
                    value = str(elem.value)[:97] + "..."
                else:
                    value = str(elem.value)
                
                item = QTreeWidgetItem(parent_item)
                item.setText(0, tag_str)
                item.setText(1, name)
                item.setText(2, vr)
                item.setText(3, value)
                
                # Add sequence items if applicable
                if elem.VR == 'SQ' and len(elem.value) > 0:
                    for i, seq_item in enumerate(elem.value):
                        seq_node = QTreeWidgetItem(item)
                        seq_node.setText(0, f"Item {i+1}")
                        seq_node.setText(1, "")
                        seq_node.setText(2, "")
                        seq_node.setText(3, "")
                        self._add_dataset_to_tree(seq_item, seq_node)
                
            except Exception as e:
                # Skip problematic elements
                continue
    
    def update_patient_info(self, dataset: pydicom.Dataset):
        """Update patient information tab."""
        # Patient demographics
        self.patient_name_label.setText(f"Name: {dataset.get('PatientName', 'N/A')}")
        self.patient_id_label.setText(f"ID: {dataset.get('PatientID', 'N/A')}")
        self.patient_sex_label.setText(f"Sex: {dataset.get('PatientSex', 'N/A')}")
        self.patient_age_label.setText(f"Age: {dataset.get('PatientAge', 'N/A')}")
        self.patient_dob_label.setText(f"DOB: {dataset.get('PatientBirthDate', 'N/A')}")
        
        # Study information
        self.study_date_label.setText(f"Date: {dataset.get('StudyDate', 'N/A')}")
        self.study_time_label.setText(f"Time: {dataset.get('StudyTime', 'N/A')}")
        self.study_desc_label.setText(f"Description: {dataset.get('StudyDescription', 'N/A')}")
        self.modality_label.setText(f"Modality: {dataset.get('Modality', 'N/A')}")
        self.institution_label.setText(f"Institution: {dataset.get('InstitutionName', 'N/A')}")
        
        # Series information
        self.series_date_label.setText(f"Date: {dataset.get('SeriesDate', 'N/A')}")
        self.series_time_label.setText(f"Time: {dataset.get('SeriesTime', 'N/A')}")
        self.series_desc_label.setText(f"Description: {dataset.get('SeriesDescription', 'N/A')}")
        self.series_number_label.setText(f"Number: {dataset.get('SeriesNumber', 'N/A')}")
    
    def filter_tags(self, text: str):
        """Filter tags tree based on search text."""
        if not text:
            # Show all items
            self._show_all_items(self.tags_tree.invisibleRootItem())
        else:
            # Hide items that don't match
            self._filter_items(self.tags_tree.invisibleRootItem(), text.lower())
    
    def _show_all_items(self, parent_item: QTreeWidgetItem):
        """Show all items in tree."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setHidden(False)
            self._show_all_items(child)
    
    def _filter_items(self, parent_item: QTreeWidgetItem, search_text: str):
        """Filter items based on search text."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # Check if item matches search
            matches = any(search_text in child.text(col).lower() for col in range(4))
            
            # Check if any child matches
            child_matches = self._filter_items(child, search_text)
            
            # Show if this item or any child matches
            child.setHidden(not (matches or child_matches))
            
        # Return True if any child was visible
        return any(not parent_item.child(i).isHidden() for i in range(parent_item.childCount()))