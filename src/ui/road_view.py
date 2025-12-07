from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QBrush, QColor, QWheelEvent
from ui.visuals import RoadVisual, JunctionVisual, CarVisual

class RoadDashboard(QWidget):
    # Signal to tell the sidebar something was clicked: (type, object)
    selection_changed = pyqtSignal(object) 

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.scene.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.scene.selectionChanged.connect(self.on_scene_selection)
        
        self.view = InteractiveGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        layout.addWidget(self.view)
        self.setLayout(layout)
        
        self.car_items = {} 

    def on_scene_selection(self):
        """ Handle item selection from the scene """
        selected_items = self.scene.selectedItems()
        if not selected_items:
            self.selection_changed.emit(None)
            return

        # Pick the first selected item to display in sidebar
        item = selected_items[0]
        if isinstance(item, RoadVisual):
            self.selection_changed.emit(item.road)
        elif isinstance(item, JunctionVisual):
            self.selection_changed.emit(item.junction)

    def draw_static_map(self, engine):
        self.scene.clear()
        self.car_items = {}
        for road in engine.roads.values():
            self.scene.addItem(RoadVisual(road))
        for junction in engine.junctions.values():
            self.scene.addItem(JunctionVisual(junction))

    def update_dynamic_agents(self, engine):
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

class InteractiveGraphicsView(QGraphicsView):
    """ Custom View to handle Zooming and Panning """
    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Anchor zoom to mouse position
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent):
        """ Zoom In/Out """
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)