from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QSlider, QLabel, QFormLayout
from PyQt6.QtCore import Qt

class ControlSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        
        main_layout = QVBoxLayout()
        
        # Section 1: Sim Controls
        sim_group = QGroupBox("Simulation Controls")
        sim_layout = QVBoxLayout()
        
        self.btn_pause = QPushButton("Pause/Resume")
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        
        sim_layout.addWidget(self.btn_pause)
        sim_layout.addWidget(QLabel("Sim Speed"))
        sim_layout.addWidget(self.slider_speed)
        sim_group.setLayout(sim_layout)
        
        # Section 2: Strategy Controls
        strat_group = QGroupBox("Optimization Strategy")
        strat_layout = QFormLayout()
        # Add strategy dropdowns here later
        strat_group.setLayout(strat_layout)
        
        # Add sections to main layout
        main_layout.addWidget(sim_group)
        main_layout.addWidget(strat_group)
        main_layout.addStretch() # Pushes everything to the top
        
        self.setLayout(main_layout)