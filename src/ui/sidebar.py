from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton, 
                             QSlider, QLabel, QFormLayout, QStackedWidget, 
                             QSpinBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class ControlSidebar(QWidget):
    # Signals to update engine parameters
    sim_speed_changed = pyqtSignal(float)
    pause_toggled = pyqtSignal()
    strategy_changed = pyqtSignal(str)
    map_changed = pyqtSignal(str)
    
    road_speed_changed = pyqtSignal(str, int)
    road_capacity_changed = pyqtSignal(str, int)
    road_block_toggled = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        
        self.main_layout = QVBoxLayout()
        
        self.create_sim_controls()
        
        self.inspector_stack = QStackedWidget()
        self.inspector_stack.addWidget(self.create_empty_inspector())
        self.inspector_stack.addWidget(QWidget()) # Index 1 (Placeholder for Road)
        self.inspector_stack.addWidget(QWidget()) # Index 2 (Placeholder for Junction)
        
        self.main_layout.addWidget(self.inspector_stack)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)
        
        self.current_selected_object = None
        
        # Reference to the dynamic label so we can update it
        self.lbl_road_car_count = None 

        self.inspector_timer = QTimer()
        self.inspector_timer.timeout.connect(self.refresh_inspector_values)
        self.inspector_timer.setInterval(100) 

    def create_sim_controls(self):
        group = QGroupBox("Global Simulation")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #444; margin-top: 20px; } QGroupBox::title { subcontrol-origin: margin; color:#ccc; left: 10px; padding: 0 3px; }")
        layout = QVBoxLayout()
        
        # --- Map Selection ---
        layout.addWidget(QLabel("Select Map:"))
        self.combo_map = QComboBox()
        self.combo_map.addItems([
            "The Grid (Pathfinding Test)", 
            "Highway with Bypass", 
            "Dual Carriageway Loop"
        ])
        self.combo_map.currentTextChanged.connect(self.map_changed.emit)
        layout.addWidget(self.combo_map)
        
        # Pause
        self.btn_pause = QPushButton("Pause Simulation")
        self.btn_pause.setStyleSheet("background-color: #d32f2f; color: white; padding: 5px; border-radius: 4px;")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause_visuals)
        self.btn_pause.clicked.connect(self.pause_toggled.emit)
        
        # Speed
        self.lbl_speed = QLabel("Time Scale: 1.0x")
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(1, 100)
        self.slider_speed.setValue(50)
        self.slider_speed.valueChanged.connect(self.update_speed_label)

        # Time Labels
        self.lbl_time_sim = QLabel("Sim Time: 0.00s")
        self.lbl_time_real = QLabel("Real Time: 0.00s")
        
        # Strategy
        self.combo_strat = QComboBox()
        self.combo_strat.addItems(["default", "least_accessed_road", "road_with_least_cars", "most_lanes_road", "highest_capacity_road"])
        self.combo_strat.currentTextChanged.connect(self.strategy_changed.emit)

        layout.addWidget(self.btn_pause)
        layout.addWidget(self.lbl_speed)
        layout.addWidget(self.slider_speed)
        layout.addWidget(self.lbl_time_sim)
        layout.addWidget(self.lbl_time_real)
        layout.addWidget(QLabel("Global Optimization Strategy:"))
        layout.addWidget(self.combo_strat)
        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def create_empty_inspector(self):
        w = QWidget()
        l = QVBoxLayout()
        lbl = QLabel("Select a Road or Junction\nto edit properties.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #777; font-style: italic;")
        l.addWidget(lbl)
        w.setLayout(l)
        return w

    def create_road_inspector(self, road):
        """ Creates a dynamic form for the specific road """
        container = QWidget()
        group = QGroupBox(f"Inspector: Road")
        group.setStyleSheet("QGroupBox { border: 1px solid #00aaff; margin-top: 10px; }")
        layout = QFormLayout()
        
        # ID Display
        lbl_id = QLabel(road.id)
        lbl_id.setStyleSheet("color: #00aaff; font-weight: bold; font-size: 7px;")
        layout.addRow("ID:", lbl_id)
        
        # Speed Limit Control
        spin_speed = QSpinBox()
        spin_speed.setRange(10, 200)
        spin_speed.setValue(road.speed)
        spin_speed.valueChanged.connect(lambda v: self.road_speed_changed.emit(road.id, v))
        layout.addRow("Speed Limit:", spin_speed)
        
        # Capacity Control
        spin_cap = QSpinBox()
        spin_cap.setRange(1, 1000)
        spin_cap.setValue(road.capacity)
        spin_cap.valueChanged.connect(lambda v: self.road_capacity_changed.emit(road.id, v))
        layout.addRow("Max Capacity:", spin_cap)

        self.lbl_road_car_count = QLabel(str(road.car_count))
        layout.addRow("Current Cars:", self.lbl_road_car_count)

        btn_block = QPushButton()
        btn_block.setFixedHeight(30)
        
        def update_btn_style(is_blocked):
            if is_blocked:
                btn_block.setText("Unblock Road")
                btn_block.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold;")
            else:
                btn_block.setText("Block Road")
                btn_block.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")

        update_btn_style(road._is_blocked)

        btn_block.clicked.connect(lambda: self._handle_block_click(road, btn_block, update_btn_style))

        layout.addRow(btn_block)
        
        group.setLayout(layout)
        vbox = QVBoxLayout()
        vbox.addWidget(group)
        container.setLayout(vbox)
        return container

    def update_context_view(self, selected_obj):
        """ Switches the inspector view based on what is selected """
        self.current_selected_object = selected_obj
        
        old_widget = self.inspector_stack.widget(1)
        if old_widget:
            self.inspector_stack.removeWidget(old_widget)
        
        if selected_obj is None:
            self.inspector_stack.setCurrentIndex(0)
            return
            
        if hasattr(selected_obj, 'lanes_count'):
            inspector = self.create_road_inspector(selected_obj)
            self.inspector_stack.insertWidget(1, inspector)
            self.inspector_stack.setCurrentIndex(1)
            self.inspector_timer.start()
        elif hasattr(selected_obj, 'in_roads'):
            self.block_button = None
            self.inspector_timer.stop()
            w = QWidget()
            l = QVBoxLayout()
            l.addWidget(QLabel(f"Junction: {selected_obj.id}"))
            w.setLayout(l)
            self.inspector_stack.insertWidget(1, w)
            self.inspector_stack.setCurrentIndex(1)

    def refresh_inspector_values(self):
        """ Called by QTimer to update dynamic labels """
        if self.current_selected_object and self.lbl_road_car_count:
            if hasattr(self.current_selected_object, 'car_count'):
                count = self.current_selected_object.car_count
                self.lbl_road_car_count.setText(str(count))

    def _handle_block_click(self, road, btn, style_updater):
        """ Handles the internal logic before emitting signals """
        new_state = not road._is_blocked
        
        self.road_block_toggled.emit(road.id, new_state)
        
        style_updater(new_state)

    def toggle_pause_visuals(self):
        if self.btn_pause.isChecked():
            self.btn_pause.setText("Resume Simulation")
            self.btn_pause.setStyleSheet("background-color: #388e3c; color: white;")
        else:
            self.btn_pause.setText("Pause Simulation")
            self.btn_pause.setStyleSheet("background-color: #d32f2f; color: white;")

    def update_speed_label(self, val):
        sim_speed = val / 50
        self.lbl_speed.setText(f"Sim Speed: {int(sim_speed * 100)}%")
        self.sim_speed_changed.emit(sim_speed)