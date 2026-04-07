"""
DICOM Viewer - Main Entry Point
Minimal MVP with PyQt6
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QMenuBar, QMenu, 
                             QStatusBar, QLabel, QFileDialog, QMessageBox,
                             QScrollArea, QTableWidget, QTableWidgetItem, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QAction, QColor, QPalette
import pydicom
import pyqtgraph as pg


class MouseClickHandler:
    """Handler for mouse click and drag events."""
    
    def __init__(self, image_view):
        self.image_view = image_view
        self._last_mouse_pos = None
        self._is_panning = False
        self._is_adjusting_wl = False
        
    def handle_click(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.scenePos()
            
    def handle_drag(self, event):
        """Handle mouse drag for panning or window/level adjustment."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_panning:
            # Pan the image
            delta = event.scenePos() - self._last_mouse_pos
            self._last_mouse_pos = event.scenePos()
            
            # Get the view box and translate
            view_box = self.image_view.getPlotItem().getViewBox()
            if view_box:
                view_box.translateBy(x=-delta.x() / view_box.width(), y=-delta.y() / view_box.height())
                
        elif event.button() == Qt.MouseButton.RightButton and self._is_adjusting_wl:
            # Adjust window/level
            delta = event.scenePos() - self._last_mouse_pos
            self._last_mouse_pos = event.scenePos()
            
            # Horizontal = window width, Vertical = window center
            self.image_view._window_width += delta.x()
            self.image_view._window_center -= delta.y()
            
            # Clamp values
            self.image_view._window_width = max(1, self.image_view._window_width)
            
            self.image_view._update_display()
            self.image_view.windowLevelChanged.emit(self.image_view._window_width, self.image_view._window_center)


class ImageViewWidget(pg.PlotWidget):
    """Custom image view widget with window/level and zoom/pan support."""
    
    windowLevelChanged = pyqtSignal(float, float)
    zoomChanged = pyqtSignal(float)
    sliceChanged = pyqtSignal(int)  # New signal for slice navigation
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Remove axes for cleaner medical image view
        self.getPlotItem().hideAxis('left')
        self.getPlotItem().hideAxis('bottom')
        
        # Image item
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)
        
        # View settings
        self._current_zoom = 1.0
        self._window_center = 0
        self._window_width = 1
        self._image_data = None
        self._total_slices = 0
        self._current_slice = 0
        
        # Mouse state
        self._last_mouse_pos = None
        self._is_panning = False
        self._is_adjusting_wl = False
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.scene().sigMouseMoved.connect(self._on_mouse_move)
        
        # Set background
        self.setBackground('#1e1e1e')
        
        # Install wheel event filter for slice navigation
        self.wheelEvent = self._handle_wheel
        
        # For mouse click tracking
        self._mouse_click_handler = MouseClickHandler(self)
        self.scene().sigMouseClicked.connect(self._mouse_click_handler.handle_click)
        self.scene().sigMouseDragged.connect(self._mouse_click_handler.handle_drag)
        
        # Install event filter for mouse press/release
        self.installEventFilter(self)
        
    def set_image(self, image_array):
        """Set the DICOM image data."""
        self._image_data = image_array
        
        # Auto calculate window/level from data
        if image_array is not None and image_array.size > 0:
            min_val = np.min(image_array)
            max_val = np.max(image_array)
            self._window_width = max_val - min_val
            self._window_center = (min_val + max_val) / 2
        
        self._update_display()
        
    def _update_display(self):
        """Update the image display with current window/level."""
        if self._image_data is None:
            return
            
        # Apply window/level transformation
        img = self._image_data.astype(np.float64)
        
        # Window/Level calculation
        wc = self._window_center
        ww = self._window_width
        
        if ww > 0:
            min_val = wc - ww / 2
            max_val = wc + ww / 2
            
            # Normalize to 0-255
            img = np.clip((img - min_val) / (max_val - min_val) * 255, 0, 255)
        
        self.image_item.setImage(img.astype(np.uint8))
        
        # Fit to view
        self.autoRange()
        
    def _handle_wheel(self, event):
        """Handle mouse wheel for zoom and slice navigation."""
        # If Ctrl is pressed, change slices
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                new_slice = max(0, self._current_slice - 1)
            else:
                new_slice = min(self._total_slices - 1, self._current_slice + 1)
            
            if new_slice != self._current_slice:
                self._current_slice = new_slice
                self.sliceChanged.emit(self._current_slice)
        else:
            # Normal wheel - zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self._current_zoom *= 1.1
            else:
                self._current_zoom /= 1.1
                
            self._current_zoom = max(0.1, min(self._current_zoom, 50))
            self.zoomChanged.emit(self._current_zoom)
            
            # Apply zoom
            self.image_item.setScale(1.0 / self._current_zoom)
    
    def set_total_slices(self, total):
        """Set total number of slices for navigation."""
        self._total_slices = total
        
    def set_current_slice(self, index):
        """Set current slice index."""
        self._current_slice = index
        
    def _on_mouse_move(self, event):
        """Track mouse position."""
        pass
    
    def _handle_mouse_press(self, event):
        """Handle mouse press for right-click W/L adjustment."""
        if event.button() == Qt.MouseButton.RightButton:
            self._mouse_click_handler._is_adjusting_wl = True
            self._mouse_click_handler._last_mouse_pos = event.pos()
            return True
        return False
    
    def _handle_mouse_release(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.RightButton:
            self._mouse_click_handler._is_adjusting_wl = False
            return True
        elif event.button() == Qt.MouseButton.LeftButton:
            self._mouse_click_handler._is_panning = False
            return True
        return False
    
    def get_window_level(self):
        """Get current window and level values."""
        return self._window_width, self._window_center
    
    def eventFilter(self, obj, event):
        """Event filter for handling mouse press/release."""
        if event.type() == QEvent.Type.MouseButtonPress:
            return self._handle_mouse_press(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            return self._handle_mouse_release(event)
        return super().eventFilter(obj, event)


class MetadataPanel(QWidget):
    """Panel to display DICOM metadata."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Metadata")
        title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Table for metadata
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Tag", "Value"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                color: #d4d4d4;
                gridline-color: #3c3c3c;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #d4d4d4;
                padding: 5px;
                border: 1px solid #3c3c3c;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
    def set_metadata(self, metadata_dict):
        """Display metadata in the table."""
        self.table.setRowCount(0)
        
        for tag, value in metadata_dict.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            tag_item = QTableWidgetItem(str(tag))
            value_item = QTableWidgetItem(str(value))
            
            tag_item.setForeground(QColor("#9cdcfe"))
            value_item.setForeground(QColor("#d4d4d4"))
            
            self.table.setItem(row, 0, tag_item)
            self.table.setItem(row, 1, value_item)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DICOM Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Current file data
        self._current_file = None
        self._series_data = []
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        
    def _apply_dark_theme(self):
        """Apply dark theme to the application."""
        dark_palette = QPalette()
        
        # Base colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(212, 212, 212))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(37, 37, 38))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(212, 212, 212))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(212, 212, 212))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(212, 212, 212))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(57, 120, 206))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(9, 71, 113))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(dark_palette)
        
        # Set style sheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #d4d4d4;
                border-bottom: 1px solid #3c3c3c;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
            }
            QLabel {
                color: #d4d4d4;
            }
        """)
        
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - vertical for image + slider
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Top section - image view and metadata
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)
        
        # Image view (center)
        self.image_view = ImageViewWidget()
        self.image_view.windowLevelChanged.connect(self._on_window_level_changed)
        self.image_view.zoomChanged.connect(self._on_zoom_changed)
        self.image_view.sliceChanged.connect(self._on_image_slice_changed)
        
        # Metadata panel (right)
        self.metadata_panel = MetadataPanel()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.image_view)
        splitter.addWidget(self.metadata_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        
        top_layout.addWidget(splitter)
        main_layout.addLayout(top_layout)
        
        # Bottom section - slice slider
        self.slice_container = QWidget()
        slice_layout = QHBoxLayout(self.slice_container)
        slice_layout.setContentsMargins(0, 5, 0, 0)
        slice_layout.setSpacing(10)
        
        # Slice slider
        self.slice_slider = QSlider(Qt.Orientation.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.setValue(0)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self._on_slice_changed)
        
        # Slice label
        self.slice_label = QLabel("Slice: - / -")
        self.slice_label.setStyleSheet("color: #d4d4d4;")
        
        slice_layout.addWidget(QLabel("Slices:"))
        slice_layout.addWidget(self.slice_slider, 1)
        slice_layout.addWidget(self.slice_label)
        
        main_layout.addWidget(self.slice_container)
        
        # Current slice index
        self._current_slice_index = 0
        
    def _setup_menu(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_file_action = QAction("Open File...", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self._open_file)
        file_menu.addAction(open_file_action)
        
        open_folder_action = QAction("Open Folder...", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.triggered.connect(self._reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        reset_wl_action = QAction("Reset Window/Level", self)
        reset_wl_action.triggered.connect(self._reset_window_level)
        view_menu.addAction(reset_wl_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Status labels
        self.file_label = QLabel("No file loaded")
        self.dimensions_label = QLabel("")
        self.window_level_label = QLabel("W/L: -- / --")
        
        self.statusbar.addWidget(self.file_label, 1)
        self.statusbar.addWidget(self.dimensions_label)
        self.statusbar.addPermanentWidget(self.window_level_label)
        
    def _open_file(self):
        """Open a single DICOM file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open DICOM File",
            "",
            "DICOM Files (*.dcm *.DCM);;All Files (*)"
        )
        
        if file_path:
            self._load_dicom_file(file_path)
            
    def _open_folder(self):
        """Open a folder containing DICOM files."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Folder",
            ""
        )
        
        if folder_path:
            self._load_dicom_folder(folder_path)
            
    def _load_dicom_file(self, file_path):
        """Load and display a DICOM file."""
        try:
            # Read DICOM file
            dcm = pydicom.dcmread(file_path)
            
            # Get pixel data
            if hasattr(dcm, 'pixel_array'):
                pixel_data = dcm.pixel_array
                
                # Display image
                self.image_view.set_image(pixel_data)
                
                # Store current file
                self._current_file = dcm
                self._series_data = [dcm]
                
                # Configure slice navigation - single file
                total_slices = len(self._series_data)
                self.slice_slider.setMaximum(total_slices - 1)
                self.slice_slider.setEnabled(total_slices > 1)
                self.slice_slider.setValue(0)
                self.image_view.set_total_slices(total_slices)
                self.image_view.set_current_slice(0)
                self.slice_label.setText(f"Slice: 1 / {total_slices}")
                
                # Update metadata
                self._update_metadata(dcm)
                
                # Update status bar
                self.file_label.setText(file_path)
                self.dimensions_label.setText(f" {pixel_data.shape[0]}x{pixel_data.shape[1]} ")
                
                self.statusbar.showMessage("File loaded successfully")
            else:
                QMessageBox.warning(self, "Error", "No pixel data found in file")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            
    def _load_dicom_folder(self, folder_path):
        """Load DICOM files from a folder."""
        import os
        import glob
        
        try:
            # Find all DICOM files in folder
            dcm_files = glob.glob(os.path.join(folder_path, "*.dcm"))
            dcm_files.extend(glob.glob(os.path.join(folder_path, "*.DCM")))
            dcm_files.extend(glob.glob(os.path.join(folder_path, "*.dcm")))
            
            if not dcm_files:
                QMessageBox.warning(self, "No Files", "No DICOM files found in folder")
                return
                
            # Sort by InstanceNumber if available
            dcm_list = []
            for f in dcm_files:
                try:
                    dcm = pydicom.dcmread(f)
                    instance_num = getattr(dcm, 'InstanceNumber', 0)
                    dcm_list.append((instance_num, f, dcm))
                except:
                    continue
                    
            dcm_list.sort(key=lambda x: x[0])
            
            if dcm_list:
                # Load first file
                _, first_file, first_dcm = dcm_list[0]
                pixel_data = first_dcm.pixel_array
                
                self.image_view.set_image(pixel_data)
                self._current_file = first_dcm
                self._series_data = [d[2] for d in dcm_list]
                
                # Configure slice navigation - series
                total_slices = len(self._series_data)
                self._current_slice_index = 0
                self.slice_slider.setMaximum(total_slices - 1)
                self.slice_slider.setEnabled(total_slices > 1)
                self.slice_slider.setValue(0)
                self.image_view.set_total_slices(total_slices)
                self.image_view.set_current_slice(0)
                self.slice_label.setText(f"Slice: 1 / {total_slices}")
                
                self._update_metadata(first_dcm)
                
                # Update status
                self.file_label.setText(first_file)
                self.dimensions_label.setText(f" {pixel_data.shape[0]}x{pixel_data.shape[1]} ")
                
                self.statusbar.showMessage(f"Loaded {len(dcm_list)} files from folder")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load folder: {str(e)}")
            
    def _update_metadata(self, dcm):
        """Update the metadata panel with DICOM tags."""
        metadata = {}
        
        # Common DICOM tags to display
        tags_to_show = [
            ('Patient Name', getattr(dcm, 'PatientName', 'N/A')),
            ('Patient ID', getattr(dcm, 'PatientID', 'N/A')),
            ('Study Date', getattr(dcm, 'StudyDate', 'N/A')),
            ('Study Time', getattr(dcm, 'StudyTime', 'N/A')),
            ('Modality', getattr(dcm, 'Modality', 'N/A')),
            ('Manufacturer', getattr(dcm, 'Manufacturer', 'N/A')),
            ('Institution Name', getattr(dcm, 'InstitutionName', 'N/A')),
            ('Study Description', getattr(dcm, 'StudyDescription', 'N/A')),
            ('Series Description', getattr(dcm, 'SeriesDescription', 'N/A')),
            ('Instance Number', getattr(dcm, 'InstanceNumber', 'N/A')),
            ('Rows', getattr(dcm, 'Rows', 'N/A')),
            ('Columns', getattr(dcm, 'Columns', 'N/A')),
            ('Bits Allocated', getattr(dcm, 'BitsAllocated', 'N/A')),
            ('Bits Stored', getattr(dcm, 'BitsStored', 'N/A')),
            ('Pixel Spacing', getattr(dcm, 'PixelSpacing', 'N/A')),
            ('Slice Thickness', getattr(dcm, 'SliceThickness', 'N/A')),
        ]
        
        for tag_name, tag_value in tags_to_show:
            if tag_value is not None and tag_value != '':
                metadata[tag_name] = tag_value
                
        self.metadata_panel.set_metadata(metadata)
        
    def _on_window_level_changed(self, window, level):
        """Handle window/level changes."""
        self.window_level_label.setText(f"W/L: {window:.0f} / {level:.0f}")
        
    def _on_zoom_changed(self, zoom):
        """Handle zoom changes."""
        pass
    
    def _on_image_slice_changed(self, index):
        """Handle slice changes from image view (mouse wheel)."""
        self._on_slice_changed(index)
        
    def _on_slice_changed(self, index):
        """Handle slice slider changes."""
        if 0 <= index < len(self._series_data):
            self._current_slice_index = index
            dcm = self._series_data[index]
            pixel_data = dcm.pixel_array
            
            # Update image view
            self.image_view.set_image(pixel_data)
            self.image_view.set_current_slice(index)
            
            # Update metadata
            self._update_metadata(dcm)
            
            # Update slice label
            total = len(self._series_data)
            self.slice_label.setText(f"Slice: {index + 1} / {total}")
            
            # Update status bar
            self.dimensions_label.setText(f" {pixel_data.shape[0]}x{pixel_data.shape[1]} ")
        
    def _reset_zoom(self):
        """Reset zoom to default."""
        self.image_view._current_zoom = 1.0
        self.image_view.image_item.setScale(1.0)
        
    def _reset_window_level(self):
        """Reset window/level to auto values."""
        if self.image_view._image_data is not None:
            min_val = np.min(self.image_view._image_data)
            max_val = np.max(self.image_view._image_data)
            self.image_view._window_width = max_val - min_val
            self.image_view._window_center = (min_val + max_val) / 2
            self.image_view._update_display()
            
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DICOM Viewer",
            "DICOM Viewer v1.0\n\n"
            "A simple DICOM image viewer built with PyQt6.\n\n"
            "Controls:\n"
            "- Right-click drag: Window/Level adjustment\n"
            "- Left-click drag: Pan\n"
            "- Mouse wheel: Zoom"
        )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("DICOM Viewer")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()