from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class DataDashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        label = QLabel("Real-time Heatmaps & Graphs Area")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("background-color: #222; color: white; border: 1px solid #444;")
        
        layout.addWidget(label)
        self.setLayout(layout)