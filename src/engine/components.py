from PyQt6.QtCore import QPointF, QPoint
import math
from typing import Callable

class Point:
    def __init__(self, x: float, y: float):
        self.x:float = x 
        self.y:float = y

    @classmethod
    def from_qt(self, qt_point: QPoint | QPointF):
        if isinstance(qt_point, (QPoint, QPointF)):
            return Point(qt_point.x(), qt_point.y())
        else:
            raise TypeError("Can only convert from types: ['QPoint', 'QPointF']")

    def to_qt(self):
        return QPointF(self.x, self.y)
    
    def distance_to(self, other):
        try:
            ox = other.x() if hasattr(other, 'x') and callable(other.x) else other.x
            oy = other.y() if hasattr(other, 'y') and callable(other.y) else other.y
            return math.hypot(self.x - ox, self.y - oy)
        except AttributeError:
            raise TypeError("Can Only calculate distance to types: ['Point', 'QPoint', 'QPointF']")
        
    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        elif isinstance(other, (QPoint, QPointF)):
            return Point(self.x + other.x(), self.y + other.y())
        elif isinstance(other, (int, float)):
            return Point(self.x + other, self.y + other)
        else:
            raise TypeError()
        
    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        elif isinstance(other, (QPoint, QPointF)):
            return Point(self.x - other.x(), self.y - other.y())
        elif isinstance(other, (int, float)):
            return Point(self.x - other, self.y - other)
        else:
            raise TypeError()
        
    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Point(self.x * scalar, self.y * scalar)
        else:
            raise TypeError()
    
    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f})"


def angle(point1, point2):
    if isinstance(point1, Point):
        x1, y1 = point1.x, point1.y
    elif isinstance(point1, (QPoint, QPointF)):
        x1, y1, = point1.x(), point1.y()
    else:
        raise TypeError("Can only calculate between these types: ['Point', 'QPoint', 'QPointF']")

    if isinstance(point2, Point):
        x2, y2 = point2.x, point2.y
    elif isinstance(point2, (QPoint, QPointF)):
        x2, y2, = point2.x(), point2.y()
    else:
        raise TypeError("Can only calculate between these types: ['Point', 'QPoint', 'QPointF']")

    dx = x2 - x1
    dy = y2 - y1

    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    
    return angle_degrees


class Junction:
    """ Represents a Node in the Graph (Junctions, Ends, Starts) """
    def __init__(self, id: str, pos: Point):
        self.id = id
        self.pos = pos
    
        self.in_roads: list[Road] = []
        self.out_roads: list[Road] = []

        # Optimization Strategy Parameters
        self.current_road_idx: int = 0
        self.access_times: list[int] = [0] * len(self.out_roads)
    
    def update_pos(self, new_pos: Point):
        self.pos = new_pos

    def add_incoming(self, road):
        self.in_roads.append(road)

    def add_outgoing(self, road):
        self.out_roads.append(road)
        self.access_times += [0]

    def __repr__(self):
        return self.id



class Road:
    """ Represents an Edge connecting two Intersections """
    def __init__(self, id:str, start: Junction, end: Junction, capacity: int, lanes: int, speed: int, blocked: bool):
        self.id = id
        self.end: Junction = end
        self.start_pos: Point = start.pos
        self.end_pos: Point = end.pos
        self.length: int = int(self.start_pos.distance_to(self.end_pos))
        self.angle: float = angle(self.start_pos, self.end_pos)

        dx = self.end_pos.x - self.start_pos.x
        dy = self.end_pos.y - self.start_pos.y
        
        if self.length > 0:
            self.unit_vector = Point(dx / self.length, dy / self.length)
        else:
            self.unit_vector = Point(0, 0)

        self.perp_vector = Point(-self.unit_vector.y, self.unit_vector.x)

        self.capacity: int = capacity
        self.n_lanes: int = lanes
        self.lane_width = 20
        self.lanes_count = [0] * self.n_lanes
        self.lane_capacity: int = self.capacity // self.n_lanes
        self.speed: int = speed
        self._is_blocked: bool = blocked
    
    @property
    def best_lane(self) -> int:
        return self.lanes_count.index(min(self.lanes_count))
    
    @property
    def available(self) -> bool:
        return (not self._is_blocked) and (self.car_count < self.capacity)
    
    @property
    def car_count(self) -> int:
        return sum(self.lanes_count)

    def block(self) -> None:
        self._is_blocked = True

    def unblock(self) -> None:
        self._is_blocked = False

    def set_speed(self, speed: int) -> None:
        self.speed = speed

    def set_capacity(self, capacity: int) -> None:
        self.capacity = capacity

    def change_lane_count(self, old_idx: int, new_idx: int):
        if 0 <= old_idx < self.n_lanes:
            self.lanes_count[old_idx] = max(0, self.lanes_count[old_idx] - 1)
        if 0 <= new_idx < self.n_lanes:
            self.lanes_count[new_idx] += 1

    def get_lane_start_offset(self, lane_idx) -> Point:
        """ Calculates the starting position of a specific lane relative to road start """
        lane_offset_scale = lane_idx - (self.n_lanes - 1) / 2.0
        offset_dist = lane_offset_scale * self.lane_width
        return self.start_pos + (self.perp_vector * offset_dist)
    
    def __repr__(self):
        return self.id

    
class Car:
    def __init__(self, spawn: Junction, strategy_callback: Callable[[Junction], Road]):
        self.junction: Junction = spawn
        self.delete: bool = False
        self.pos: Point = self.junction.pos
        self.road: Road = None
        self.angle: float = 0
        self.road_progress: float = 0
        self.lane_idx: int = 0
        self.visual_lane_offset:float = 0.0
        self.strategy_callback: Callable[[Junction], Road] = strategy_callback

        
    def move(self, dt: float):
        if self.delete or not self.road:
            return

        dist_to_travel = dt * self.road.speed
        
        if self.road_progress + dist_to_travel >= self.road.length:
            excess_distance = (self.road_progress + dist_to_travel) - self.road.length
            
            self.junction = self.road.end
            self.road.change_lane_count(self.lane_idx, -1) 
            self.resolve_junction()
            
            if self.delete:
                return

            self.road_progress = excess_distance
            
            self.road_progress = min(self.road_progress, self.road.length)
        else:
            self.road_progress += dist_to_travel

        if self.road_progress > 0: 
            target_lane = self.road.best_lane
            if target_lane != self.lane_idx:
                self.road.change_lane_count(self.lane_idx, target_lane)
                self.lane_idx = target_lane

        point_on_center_line = self.road.start_pos + (self.road.unit_vector * self.road_progress)
        target_offset = self.lane_idx - (self.road.n_lanes - 1) / 2.0
        self.visual_lane_offset += (target_offset - self.visual_lane_offset) * 0.1 # smoothing factor

        lane_offset_vec = self.road.perp_vector * (self.visual_lane_offset * self.road.lane_width)
        self.pos = point_on_center_line + lane_offset_vec

    def resolve_junction(self):
        new_road = self.strategy_callback(self.junction)
        
        if new_road and new_road.start_pos:
            self.road = new_road
            self.angle = new_road.angle
            self.lane_idx = self.road.best_lane
            self.road.change_lane_count(-1, self.lane_idx) 
           
        else:
            self.delete = True

  