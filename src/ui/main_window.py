from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, 
                             QHBoxLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer

from ui.sidebar import ControlSidebar
from ui.road_view import RoadDashboard
from ui.data_view import DataDashboard
from ui.maps import MapLoader
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
        splitter.setSizes([280, 920])
        
        main_layout.addWidget(splitter)
        
        # Connect Sidebar Signals
        self.sidebar.pause_toggled.connect(self.toggle_pause_engine)
        self.sidebar.sim_speed_changed.connect(self.update_sim_speed)
        self.sidebar.strategy_changed.connect(self.update_optimization_strategy)
        self.sidebar.road_block_toggled.connect(self.toggle_road_block)
        self.sidebar.map_changed.connect(self.change_map) # <--- Map Switching
        
        self.sidebar.road_speed_changed.connect(self.apply_road_speed)
        self.sidebar.road_capacity_changed.connect(self.apply_road_capacity)
        
        self.road_view.selection_changed.connect(self.sidebar.update_context_view)

        # 2. Setup Engine & Map
        self.engine = SimulationEngine()
        self.current_map_name = "The Grid (Pathfinding Test)"
        self.load_current_map()
        
        self.current_strategy_name = "default"
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16) # ~60 FPS target (Update loop runs faster for smoothness)

        self.engine.paused = False

    def load_current_map(self):
        """ Resets engine and loads the selected map """
        # Pause to prevent update errors during reload
        was_paused = self.engine.paused
        self.engine.pause()
        
        # Create fresh engine instance to ensure total cleanup
        # (Alternatively, you could write a engine.clear() method)
        new_engine = SimulationEngine()
        
        new_engine.paused = True # Start paused while loading
        
        # Load Map Logic
        MapLoader.load_map(new_engine, self.current_map_name)
        
        # Replace engine reference
        self.engine = new_engine
        
        # Reset View
        self.road_view.draw_static_map(self.engine)
        self.sidebar.update_context_view(None) # Clear inspector
        
        if not was_paused:
            self.engine.paused = False

    def change_map(self, map_name):
        self.current_map_name = map_name
        self.load_current_map()

    def game_loop(self):
        """ Main Simulation Loop using Real Delta Time """
        
        dt = 0.05

        # Update Engine
        self.engine.update(dt)
        
        # Update UI Labels
        self.sidebar.lbl_time_real.setText(f"Real Time: {self.engine.real_elapsed_time:.1f}s")
        self.sidebar.lbl_time_sim.setText(f"Sim Time: {self.engine.sim_elapsed_time:.1f}s")
        
        # Update Visuals
        self.road_view.update_dynamic_agents(self.engine)
        
        # Spawner Logic (Weighted by simulation speed to stay consistent)
        import random
        # Spawn chance relative to dt. E.g., 1 car per ~2 seconds
        if not self.engine.paused and self.engine.junctions:
            spawn_chance = dt * self.engine.simulation_speed_modifier * 0.5 
            if random.random() < spawn_chance:
                j_id = random.choice(list(self.engine.junctions.keys()))
                self.engine.spawn_car(j_id, strategy_name=self.current_strategy_name)

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
            else:
                road.unblock()
            self.road_view.scene.update()

    def update_sim_speed(self, val):
        self.engine.set_simulation_speed(val)

    def update_optimization_strategy(self, strat_name):
        self.engine.set_optimization_strategy(strat_name)

    def apply_road_speed(self, road_id, new_speed):
        if road_id in self.engine.roads:
            self.engine.roads[road_id].speed = new_speed

    def apply_road_capacity(self, road_id, new_cap):
        if road_id in self.engine.roads:
            self.engine.roads[road_id].capacity = new_cap
            self.engine.roads[road_id].lane_capacity = new_cap // self.engine.roads[road_id].n_lanes