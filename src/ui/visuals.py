from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItemGroup
from PyQt6.QtCore import Qt, QLineF
from PyQt6.QtGui import QPen, QBrush, QColor

from engine.components import Car, Road, Junction

import random

colors = ["#FF0000",  
        "#aaFF00",
        "#00aaFF",] 

class RoadVisual(QGraphicsItemGroup):
    """ 
    Visual representation of a Road. 
    Draws a thick gray line for asphalt and dashed lines for lanes.
    """ 
    def __init__(self, road_data: Road):
        super().__init__()
        self.road = road_data
        
        start = self.road.start_pos.to_qt()
        end = self.road.end_pos.to_qt()
        
        total_width = self.road.n_lanes * 20
        
        asphalt = QGraphicsLineItem(QLineF(start, end))
        pen = QPen(QColor("#333333")) # Dark Gray
        pen.setWidth(total_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        asphalt.setPen(pen)
        asphalt.setZValue(0)
        self.addToGroup(asphalt)
        
        if self.road.n_lanes > 1:

            center_line = QGraphicsLineItem(QLineF(start, end))
            dashed_pen = QPen(QColor("yellow"))
            dashed_pen.setWidth(2)
            dashed_pen.setStyle(Qt.PenStyle.DashLine)
            center_line.setPen(dashed_pen)
            center_line.setZValue(1)
            self.addToGroup(center_line)

class JunctionVisual(QGraphicsEllipseItem):
    """ Visual Representation of a Junction """
    def __init__(self, junction_data: Junction):
        super().__init__()
        radius = 15
        
        x = junction_data.pos.x - radius
        y = junction_data.pos.y - radius
        
        self.setRect(x, y, radius*2, radius*2)
        
        self.setBrush(QBrush(QColor("#555555")))
        self.setPen(QPen(QColor("white"), 2))
        self.setZValue(2) 

class CarVisual(QGraphicsRectItem):
    """ Visual representation of a Car """
    def __init__(self, car_data: Car, color: str = "random"):
        super().__init__(-10, -5, 20, 10)
        self.car_data = car_data

        if color == "random":
            choice = random.choice(colors)
            self.setBrush(QBrush(QColor(choice)))
        else:    
            self.setBrush(QBrush(QColor(color)))

        
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setZValue(10)
        
        self.setTransformOriginPoint(0, 0)
        
        self.update_visuals()

    def update_visuals(self):
        """ Syncs visual position/rotation with engine data """
        pos = self.car_data.pos.to_qt()
        self.setPos(pos)
        self.setRotation(self.car_data.angle)