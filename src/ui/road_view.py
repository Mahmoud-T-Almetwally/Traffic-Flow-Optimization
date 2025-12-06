from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor

from ui.visuals import RoadVisual, JunctionVisual, CarVisual
from engine.simulation_engine import SimulationEngine
from engine.components import Car


class RoadDashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        
        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setStyleSheet("border: none;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.car_items: dict[Car, CarVisual] = {} 

    def draw_static_map(self, engine: SimulationEngine):
        """ Called once at startup to draw roads and junctions """
        self.scene.clear()
        self.car_items = {}

        for road in engine.roads.values():
            visual = RoadVisual(road)
            self.scene.addItem(visual)

        for junction in engine.junctions.values():
            visual = JunctionVisual(junction)
            self.scene.addItem(visual)

    def update_dynamic_agents(self, engine: SimulationEngine):
        """ Called every frame to update cars """
        
        active_cars = set(engine.cars)
        
        for car in engine.cars:
            if car not in self.car_items:
                visual = CarVisual(car)
                self.scene.addItem(visual)
                self.car_items[car] = visual
            else:
                self.car_items[car].update_visuals()
        
        dead_cars = [c for c in self.car_items if c not in active_cars]
        for c in dead_cars:
            self.scene.removeItem(self.car_items[c])
            del self.car_items[c]