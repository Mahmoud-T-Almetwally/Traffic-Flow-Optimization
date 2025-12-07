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
        
        self.sidebar.pause_toggled.connect(self.toggle_pause_engine)
        self.sidebar.sim_speed_changed.connect(self.update_sim_speed)
        self.sidebar.strategy_changed.connect(self.update_spawning_strategy)
        self.sidebar.road_block_toggled.connect(self.toggle_road_block)
        
        # 2. Connect Sidebar Inspector Signals
        self.sidebar.road_speed_changed.connect(self.apply_road_speed)
        self.sidebar.road_capacity_changed.connect(self.apply_road_capacity)
        
        # 3. Connect View Selection to Sidebar
        self.road_view.selection_changed.connect(self.sidebar.update_context_view)

        # 2. Setup Simulation Engine
        self.engine = SimulationEngine()
        self.bootstrap_test_map() # Create some roads
        
        # 3. Initial Draw
        self.road_view.draw_static_map(self.engine)
        
        self.current_strategy_name = "default"

        # 4. Setup Game Loop Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(30) # 30ms ~ 33 FPS

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
                j_id = random.choice(list(self.engine.junctions.keys()))
                self.engine.spawn_car(j_id, "default")

    def toggle_pause_engine(self):
        if self.engine.paused:
            self.engine.start()
        else:
            self.engine.pause()

    def toggle_road_block(self, road_id: str, should_block: bool):
        if road_id in self.engine.roads:
            road = self.engine.roads[road_id]
            if should_block:
                road.block()
                print(f"Road {road_id} BLOCKED")
            else:
                road.unblock()
                print(f"Road {road_id} UNBLOCKED")
            
            self.road_view.scene.update()

    def update_sim_speed(self, val):
        self.engine.set_simulation_speed(val)

    def update_spawning_strategy(self, strat_name):
        self.current_strategy_name = strat_name

    def apply_road_speed(self, road_id, new_speed):
        if road_id in self.engine.roads:
            self.engine.roads[road_id].speed = new_speed

    def apply_road_capacity(self, road_id, new_cap):
        if road_id in self.engine.roads:
            self.engine.roads[road_id].capacity = new_cap
            self.engine.roads[road_id].lane_capacity = new_cap // self.engine.roads[road_id].n_lanes
            print(f"Updated {road_id} capacity to {new_cap}")

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