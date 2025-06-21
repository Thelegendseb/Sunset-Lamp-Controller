import sys
import asyncio
import numpy as np
from PIL import ImageGrab
from PyQt6 import QtGui
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QColorDialog, QTextEdit, QSlider)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QIcon
from bleak import BleakClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lightController import set_color, ADDRESS
import time

class LightControlThread(QThread):
    status_update = pyqtSignal(str)
    color_update = pyqtSignal(int, int, int)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.screen_sync_mode = False
        self.manual_color = (255, 255, 255)  # RGB
        self.brightness = 100
        self.brightness_override = None  # For manual brightness in screen sync mode
        
    def set_manual_color(self, r, g, b):
        self.manual_color = (r, g, b)
        
    def set_brightness(self, brightness):
        self.brightness = brightness
        
    def set_brightness_override(self, brightness):
        """Override brightness in screen sync mode"""
        self.brightness_override = brightness
        
    def set_screen_sync(self, enabled):
        self.screen_sync_mode = enabled
        if not enabled:
            self.brightness_override = None  # Clear override when leaving screen sync
        
    def run(self):
        asyncio.run(self.light_control_loop())
        
    async def light_control_loop(self):
        try:
            self.status_update.emit("🔌 Connecting to device...")
            async with BleakClient(ADDRESS, timeout=5.0) as client:
                self.status_update.emit("✅ Connected")
                
                while self.running:
                    if self.screen_sync_mode:
                        # Get color from screen
                        r, g, b = self.get_screen_color()
                        
                        # Use manual brightness override if set, otherwise calculate from screen
                        if self.brightness_override is not None:
                            brightness = self.brightness_override
                        else:
                            luminance = 0.299*r + 0.587*g + 0.114*b
                            brightness = max(5, int((luminance / 255) * 100))
                    else:
                        # Use manual color and brightness
                        r, g, b = self.manual_color
                        brightness = self.brightness
                    
                    # Send color to light
                    await set_color(client, r, g, b, brightness=brightness)
                    
                    # Update GUI
                    self.color_update.emit(r, g, b)
                    
                    # Small delay to not overwhelm the connection
                    await asyncio.sleep(0.05)
                    
        except Exception as e:
            self.status_update.emit(f"❌ Error: {str(e)}")
            
    def get_screen_color(self):
        """Get average screen color with enhancement for dark colors"""
        screenshot = ImageGrab.grab()
        img_array = np.array(screenshot)
        avg_color = np.mean(img_array.reshape(-1, 3), axis=0).astype(int)
        r, g, b = avg_color
        
        # Enhance dark colors
        luminance = 0.299*r + 0.587*g + 0.114*b
        if luminance < 40:
            max_component = max(r, g, b)
            if max_component > 0:
                scale = min(255 / max_component, 3)
                r = min(255, int(r * scale))
                g = min(255, int(g * scale))
                b = min(255, int(b * scale))
        
        return r, g, b
            
    def stop_thread(self):
        self.running = False
        
    def start_thread(self):
        self.running = True

class LightControllerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.light_thread = None
        self.current_color = QColor(255, 255, 255)
        self.saved_manual_color = QColor(255, 255, 255)  # Store manual color when in screen sync
        self.brightness = 100
        self.connected = False
        self.in_screen_sync = False
        self.slider_being_dragged = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Sunset Lamp Controller")
        self.setGeometry(100, 100, 400, 550)
        self.setMaximumSize(450, 600) 
        self.setWindowFlags(Qt.WindowType.Window | 
                        Qt.WindowType.WindowCloseButtonHint | 
                        Qt.WindowType.WindowMinimizeButtonHint)

        icon_path = resource_path("ico.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Sunset Lamp Controller")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("🔴 Disconnected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 5px; font-size: 14px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Color display
        self.color_display = QLabel()
        self.color_display.setFixedHeight(80)
        self.update_color_display()
        layout.addWidget(self.color_display)
        
        # Brightness slider
        brightness_layout = QVBoxLayout()
        brightness_label = QLabel("💡 Brightness")
        brightness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brightness_label.setStyleSheet("font-weight: bold; margin: 5px;")
        brightness_layout.addWidget(brightness_label)
        
        slider_layout = QHBoxLayout()
        
        moon_label = QLabel("🌙")
        moon_label.setStyleSheet("font-size: 20px; margin: 0px 5px;")
        slider_layout.addWidget(moon_label)
        
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setMinimum(1)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 2px solid #ddd;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2c3e50, stop: 0.5 #f39c12, stop: 1 #f1c40f);
                height: 12px;
                border-radius: 8px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #ecf0f1, stop: 1 #bdc3c7);
                border: 2px solid #95a5a6;
                width: 22px;
                height: 22px;
                margin: -7px 0;
                border-radius: 13px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 2px solid #6c757d;
            }
        """)
        self.brightness_slider.valueChanged.connect(self.brightness_changed)
        self.brightness_slider.sliderPressed.connect(self.slider_pressed)
        self.brightness_slider.sliderReleased.connect(self.slider_released)
        slider_layout.addWidget(self.brightness_slider)
        
        sun_label = QLabel("☀️")
        sun_label.setStyleSheet("font-size: 20px; margin: 0px 5px;")
        slider_layout.addWidget(sun_label)
        
        brightness_layout.addLayout(slider_layout)
        
        self.brightness_value_label = QLabel("100%")
        self.brightness_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_value_label.setStyleSheet("color: #666; margin: 5px; font-weight: bold;")
        brightness_layout.addWidget(self.brightness_value_label)
        
        layout.addLayout(brightness_layout)
        
        # Color picker
        self.color_button = QPushButton("🎨 Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        self.color_button.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(self.color_button)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        
        self.sync_btn = QPushButton("📺 Screen Sync")
        self.sync_btn.clicked.connect(self.toggle_screen_sync)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.sync_btn)
        layout.addLayout(button_layout)
        
        # Log
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(80)
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
    def slider_pressed(self):
        """Called when user starts dragging the slider"""
        self.slider_being_dragged = True
        
    def slider_released(self):
        """Called when user stops dragging the slider"""
        self.slider_being_dragged = False
        # Now log the brightness change
        if self.light_thread:
            if self.in_screen_sync:
                self.log(f"💡 Brightness override set to {self.brightness}% (Screen Sync mode)")
            else:
                self.log(f"💡 Brightness set to {self.brightness}%")
        
    def brightness_changed(self, value):
        self.brightness = value
        self.brightness_value_label.setText(f"{value}%")
        
        if self.light_thread:
            if self.in_screen_sync:
                # In screen sync mode, use brightness override
                self.light_thread.set_brightness_override(value)
            else:
                # Normal mode
                self.light_thread.set_brightness(value)
                self.update_color_display()
            
    def update_color_display(self):
        # Show color with brightness effect (only for manual colors)
        if not self.in_screen_sync:
            brightness_factor = self.brightness / 100.0
            display_r = int(self.current_color.red() * brightness_factor)
            display_g = int(self.current_color.green() * brightness_factor)
            display_b = int(self.current_color.blue() * brightness_factor)
        else:
            # In screen sync, show actual screen color
            display_r = self.current_color.red()
            display_g = self.current_color.green()
            display_b = self.current_color.blue()
        
        self.color_display.setStyleSheet(
            f"background-color: rgb({display_r}, {display_g}, {display_b}); "
            f"border: 2px solid #ccc; border-radius: 5px;"
        )
        
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Choose Color")
        if color.isValid():
            self.current_color = color
            self.saved_manual_color = color  # Save for when exiting screen sync
            self.update_color_display()
            
            if self.light_thread:
                self.light_thread.set_manual_color(color.red(), color.green(), color.blue())
                
            self.log(f"🎨 Color selected: RGB({color.red()}, {color.green()}, {color.blue()})")
            
    def toggle_connection(self):
        if not self.connected:
            self.start_light_control()
        else:
            self.stop_light_control()
            
    def start_light_control(self):
        self.light_thread = LightControlThread()
        self.light_thread.status_update.connect(self.update_status)
        self.light_thread.color_update.connect(self.update_display_color)
        
        # Set initial values
        self.light_thread.set_manual_color(
            self.current_color.red(), 
            self.current_color.green(), 
            self.current_color.blue()
        )
        self.light_thread.set_brightness(self.brightness)
        
        self.light_thread.start_thread()
        self.light_thread.start()
        
        self.connect_btn.setText("🔌 Disconnect")
        self.sync_btn.setEnabled(True)
        self.connected = True
        self.log("🔌 Starting light control...")
        
    def stop_light_control(self):
        if self.light_thread:
            self.light_thread.stop_thread()
            self.light_thread.wait(2000)
            self.light_thread = None
            
        self.connected = False
        self.in_screen_sync = False
        self.status_label.setText("🔴 Disconnected")
        self.connect_btn.setText("🔌 Connect")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("📺 Screen Sync")
        self.color_button.setEnabled(True)  # Re-enable color button
        self.log("🔌 Disconnected")
        
    def toggle_screen_sync(self):
        if self.sync_btn.text() == "📺 Screen Sync":
            if self.light_thread:
                # Save current manual color before entering screen sync
                self.saved_manual_color = self.current_color
                
                self.light_thread.set_screen_sync(True)
                self.sync_btn.setText("⏹ Stop Sync")
                self.status_label.setText("📺 Screen sync active")
                self.color_button.setEnabled(False)  # Disable color picker
                self.in_screen_sync = True
                self.log("📺 Screen sync enabled")
        else:
            if self.light_thread:
                self.light_thread.set_screen_sync(False)
                self.sync_btn.setText("📺 Screen Sync")
                self.status_label.setText("✅ Connected")
                self.color_button.setEnabled(True)  # Re-enable color picker
                self.in_screen_sync = False
                
                # Restore saved manual color
                self.current_color = self.saved_manual_color
                self.update_color_display()
                
                # Update thread with saved color
                self.light_thread.set_manual_color(
                    self.saved_manual_color.red(),
                    self.saved_manual_color.green(), 
                    self.saved_manual_color.blue()
                )
                
                self.log("⏹ Screen sync disabled")
                
    def update_status(self, message):
        self.status_label.setText(message)
        # Only log status updates, not every single one
        if "Connected" in message or "Error" in message:
            self.log(message)
        
    def update_display_color(self, r, g, b):
        # Update display color from screen sync
        if self.light_thread and self.light_thread.screen_sync_mode:
            self.current_color = QColor(r, g, b)
            self.update_color_display()
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        self.stop_light_control()
        event.accept()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    icon_path = resource_path("ico.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    window = LightControllerGUI()
    window.show()
    sys.exit(app.exec())
    

if __name__ == "__main__":
    main()