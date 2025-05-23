from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox, QTabWidget, QFormLayout
from PyQt6.QtCore import Qt

class AdvancedTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QFormLayout()
        self.setLayout(self.layout)

        # Update Frequency Field (1-70 Hz)
        self.freq_input = QSpinBox()
        self.freq_input.setRange(1, 70)
        self.layout.addRow("Update Frequency (Hz):", self.freq_input)

        # IP Field for Servo Arm 1
        self.ip_input1 = QLineEdit()
        self.layout.addRow("Left servo motor IP:", self.ip_input1)

        # IP Field for Servo Arm 2
        self.ip_input2 = QLineEdit()
        self.layout.addRow("Right servo motor IP:", self.ip_input2)

    def get_freq(self):
        return self.freq_input.value()
    
    def get_left_motor(self):
        return self.ip_input1.text()
    
    def get_right_motor(self):
        return self.ip_input2.text()
    
    def set_freq(self, val):
        return self.freq_input.setValue(val)
    
    def set_left_motor(self, val):
        return self.ip_input1.setText(val)
    
    def set_right_motor(self, val):
        return self.ip_input2.setText(val)