from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItemGroup, QGraphicsItem, QStyle
from PyQt6.QtCore import Qt, QLineF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainterPathStroker

import random

from engine.components import Road, Car, Junction

colors = ["#00aaff", "#ff0000", "#00ffaa"]

class RoadVisual(QGraphicsItemGroup):
    """ 
    Visual representation of a Road. 
    """ 
    def __init__(self, road_data:Road):
        super().__init__()
        self.road = road_data
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        start = self.road.start_pos.to_qt()
        end = self.road.end_pos.to_qt()
        
        self.total_width = self.road.n_lanes * 20

        self.default_pen = QPen(QColor("#333333"))
        self.default_pen.setWidth(self.total_width)
        self.default_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        self.selected_pen = QPen(QColor("#556677")) 
        self.selected_pen.setWidth(self.total_width)
        self.selected_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        self.blocked_pen = QPen(QColor("#8B0000"))
        self.blocked_pen.setWidth(self.total_width)
        self.blocked_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        self.blocked_selected_pen = QPen(QColor("#FF4500"))
        self.blocked_selected_pen.setWidth(self.total_width)
        self.blocked_selected_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        self.asphalt = QGraphicsLineItem(QLineF(start, end))
        self.asphalt.setPen(self.default_pen)
        self.addToGroup(self.asphalt)
        
        if self.road.n_lanes > 1:
            center_line = QGraphicsLineItem(QLineF(start, end))
            dashed_pen = QPen(QColor("yellow"))
            dashed_pen.setWidth(2)
            dashed_pen.setStyle(Qt.PenStyle.DashLine)
            center_line.setPen(dashed_pen)
            center_line.setZValue(1)
            self.addToGroup(center_line)

    def shape(self):
        """ 
        This defines the exact 'hitbox' of the item. 
        Instead of a bounding rectangle (which includes empty space for diagonal roads),
        we return a path that follows the exact shape of the road.
        """
        path = QPainterPath()
        start = self.road.start_pos.to_qt()
        end = self.road.end_pos.to_qt()
        
        path.moveTo(start)
        path.lineTo(end)
        
        stroker = QPainterPathStroker()
        stroker.setWidth(self.total_width)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        return stroker.createStroke(path)

    def paint(self, painter, option, widget):
        """
        Handle coloring logic and prevent default selection borders.
        """
        
        is_blocked = self.road._is_blocked
        is_selected = self.isSelected()

        if is_blocked and is_selected:
            self.asphalt.setPen(self.blocked_selected_pen)
        elif is_blocked:
            self.asphalt.setPen(self.blocked_pen)
        elif is_selected:
            self.asphalt.setPen(self.selected_pen)
        else:
            self.asphalt.setPen(self.default_pen)

        option.state &= ~QStyle.StateFlag.State_Selected

        super().paint(painter, option, widget)

class JunctionVisual(QGraphicsEllipseItem):
    def __init__(self, junction_data: Junction):
        super().__init__()
        self.junction = junction_data
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        radius = 15
        x = junction_data.pos.x - radius
        y = junction_data.pos.y - radius
        self.setRect(x, y, radius*2, radius*2)
        
        self.default_brush = QBrush(QColor("#555555"))
        self.selected_brush = QBrush(QColor("#ff9900"))
        
        self.setBrush(self.default_brush)
        self.setPen(QPen(QColor("white"), 2))
        self.setZValue(2)

    def paint(self, painter, option, widget):
        if self.isSelected():
            self.setBrush(self.selected_brush)
        else:
            self.setBrush(self.default_brush)
            
        option.state &= ~QStyle.StateFlag.State_Selected
        
        super().paint(painter, option, widget)

class CarVisual(QGraphicsRectItem):
    def __init__(self, car_data: Car, color: str = "random"):
        super().__init__(-10, -5, 20, 10)
        self.car_data = car_data
        if color == "random":
            color = random.choice(colors)
        self.setBrush(QBrush(QColor(color))) 
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setZValue(10) 
        
        self.setTransformOriginPoint(0, 0)
        
        self.update_visuals()

    def update_visuals(self):
        pos = self.car_data.pos.to_qt()
        self.setPos(pos)
        self.setRotation(self.car_data.angle)