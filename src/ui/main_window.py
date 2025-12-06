from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, 
                             QHBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer

from ui.sidebar import ControlSidebar
from ui.road_view import RoadDashboard
from ui.data_view import DataDashboard
from engine.simulation_engine import SimulationEngine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Traffic Optimization System")
        self.resize(1200, 800)
        
        # 1. Setup UI Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar = ControlSidebar()
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 0; }")
        
        self.road_view = RoadDashboard()
        self.data_view = DataDashboard()
        
        self.tabs.addTab(self.road_view, "Map View")
        self.tabs.addTab(self.data_view, "Data Analysis")
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setSizes([250, 950])
        
        main_layout.addWidget(splitter)
        
        # 2. Setup Simulation Engine
        self.engine = SimulationEngine()
        self.bootstrap_test_map() # Create some roads
        
        # 3. Initial Draw
        self.road_view.draw_static_map(self.engine)
        
        # 4. Setup Game Loop Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(30) # 30ms ~ 33 FPS
        
        # 5. Connect Sidebar Signals
        self.sidebar.btn_pause.clicked.connect(self.toggle_pause)
        # Initialize sidebar with engine state
        self.engine.paused = False # Start running

    def game_loop(self):
        """ Main Simulation Loop """
        # 1. Update Physics
        # dt is fixed at 0.033 for now, later you can use actual delta time
        self.engine.update(dt=0.05) 
        
        # 2. Update Visuals
        self.road_view.update_dynamic_agents(self.engine)
        
        # 3. Simple Spawner for testing
        # Spawn a car every ~100 frames
        import random
        if random.randint(0, 50) == 0:
            if self.engine.junctions:
                # Pick a random junction to spawn
                j_id = random.choice(list(self.engine.junctions.keys()))
                self.engine.spawn_car(j_id, "default")

    def toggle_pause(self):
        if self.engine.paused:
            self.engine.start()
        else:
            self.engine.pause()

    def bootstrap_test_map(self):
        """ Hardcoded map for testing """
        # Triangle Loop
        j1 = self.engine.create_junction(100, 100)
        j2 = self.engine.create_junction(500, 100)
        j3 = self.engine.create_junction(300, 400)
        
        # Connect them
        props = {"capacity": 10, "speed": 100, "lanes": 2}
        
        # Clockwise
        self.engine.create_road(j1, j2, props)
        self.engine.create_road(j2, j3, props)
        self.engine.create_road(j3, j1, props)
        
        # Counter-Clockwise (Two-way roads)
        # self.engine.create_road(j2, j1, props)
        # self.engine.create_road(j3, j2, props)
        # self.engine.create_road(j1, j3, props)