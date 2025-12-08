from PyQt6.QtCore import QPointF, QPoint, QTimer
import math
import numpy as np
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

        self.current_road_idx: int = 0
    
    def update_pos(self, new_pos: Point):
        self.pos = new_pos

    def add_incoming(self, road):
        self.in_roads.append(road)

    def add_outgoing(self, road):
        self.out_roads.append(road)

    def __repr__(self):
        return self.id



class Road:
    """ Represents an Edge connecting two Junctions """
    def __init__(self, id:str, start: Junction, end: Junction, capacity: int, lanes: int, speed: int, blocked: bool, go_duration: float = 10, stop_duration: float = 5):
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
        self.stopped: bool = False
        self.stop_duration: float = stop_duration
        self.go_duration: float = go_duration
        self.light_timer: float = 0.0
        self.access_times: int = 0
        self.cars: list[Car] = []
    
    @property
    def best_lane(self) -> int:
        return self.lanes_count.index(min(self.lanes_count))
    
    @property
    def available(self) -> bool:
        return (not self._is_blocked) and (self.car_count < self.capacity)
    
    @property
    def car_count(self) -> int:
        return len(self.cars)
    
    def update_lights(self, dt: float):
        """ Called by SimulationEngine to cycle lights based on Simulation Time """
        self.light_timer += dt
        
        if self.stopped:
            if self.light_timer >= self.stop_duration:
                self.stopped = False 
                self.light_timer = 0.0
        else:
            if self.light_timer >= self.go_duration:
                self.stopped = True 
                self.light_timer = 0.0

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
    
    def add_car(self, car) -> int:
        """ Adds car, increments count, returns assigned lane. """
        self.cars.append(car)
        self.access_times += 1
        lane = self.best_lane
        self.lanes_count[lane] += 1
        return lane

    def remove_car(self, car_id: str):
        for i in range(len(self.cars)):
            if self.cars[i].id == car_id:
                self.cars.pop(i)
                return

    def get_space_at_start(self, lane_idx: int) -> float:
        """ 
        Returns the distance (pixels) from the start of the road 
        to the rear bumper of the last car in the specified lane. 
        Returns Road Length if empty.
        """
        min_progress = self.length
        found = False
        
        for car in self.cars:
            if car.lane_idx == lane_idx:
                if car.road_progress < min_progress:
                    min_progress = car.road_progress
                    found = True
        
        if not found:
            return float(self.length)
        
        return max(0.0, min_progress - 15.0)
    
    def can_reach(self, target_node: Junction) -> bool:
        """ BFS to check if a path exists """
        if self.end == target_node:
            return True
            
        visited = {self.end}
        queue = [self.end]
        
        while queue:
            current = queue.pop(0)
            if current == target_node:
                return True
            
            for road in current.out_roads:
                next_node = road.end
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append(next_node)
                    
        return False
    
    def __repr__(self):
        return self.id

    
class Car:
    def __init__(self, car_id:str,  spawn: Junction, goal: Junction,strategy_callback: Callable[[Junction, Junction], Road]):
        self.id: str = car_id
        self.junction: Junction = spawn
        self.delete: bool = False
        self.pos: Point = self.junction.pos
        self.goal: Junction = goal
        self.road: Road = None
        self.angle: float = 0
        self.road_progress: float = 0
        self.lane_idx: int = 0
        self.visual_lane_offset:float = 0.0
        self.strategy_callback: Callable[[Junction, Junction], Road] = strategy_callback
        self.collision_streak: int = 0

        
    def move(self, dt: float):
        if self.delete or not self.road:
            return

        dist_to_obstacle = self._dist_to_obstacle

        braking_factor = 1.0
        SAFE_BRAKING_DIST = 60.0
        
        if dist_to_obstacle < SAFE_BRAKING_DIST:
            ratio = dist_to_obstacle / SAFE_BRAKING_DIST
            braking_factor = max(0.0, ratio * ratio)
        
        target_speed = self.road.speed * braking_factor
        
        if dist_to_obstacle < 5.0:
            target_speed = 0.0

        dist_to_travel = dt * target_speed

        max_physical_move = max(0.0, dist_to_obstacle - 2.0)
        dist_to_travel = min(dist_to_travel, max_physical_move)

        if self.road_progress + dist_to_travel >= self.road.length:
            
            if self.road.stopped:
                self.road_progress = min(self.road_progress + dist_to_travel, self.road.length - 1.0)
                self._update_visual_pos()
                return
            
            if self.road.end == self.goal:
                old_road = self.road
                old_road.remove_car(self.id)
                old_road.change_lane_count(self.lane_idx, -1)
                self.road = None
                self.delete = True
                return

            excess = (self.road_progress + dist_to_travel) - self.road.length
            
            next_road = self.strategy_callback(self.junction, self.goal)

            if next_road:
                target_lane = next_road.best_lane
                space_on_next_road = next_road.get_space_at_start(target_lane)
                
                if space_on_next_road < (excess + 15.0):
                    self.road_progress = self.road.length - 1.0
                    self._update_visual_pos()
                    return

                old_road = self.road
                old_road.remove_car(self.id)
                old_road.change_lane_count(self.lane_idx, -1)

                self.junction = self.road.end
                
                self.road = next_road
                self.lane_idx = self.road.add_car(self)
                self.angle = self.road.angle
                
                self.road_progress = excess
                self.visual_lane_offset = self.lane_idx - (self.road.n_lanes - 1) / 2.0
            else:
                old_road = self.road
                old_road.remove_car(self.id)
                old_road.change_lane_count(self.lane_idx, -1)
                
                self.road = None 
                self.delete = True
                return 
        else:
            self.road_progress += dist_to_travel

        target_lane = self.road.best_lane
        if self._safe_to_change_lanes(target_lane, target_speed, self.road_progress + dist_to_travel):
            self.road.change_lane_count(self.lane_idx, target_lane)
            self.lane_idx = target_lane

        self._update_visual_pos()

    def resolve_junction(self):
        """ Only called on spawn to place car initially """
        new_road = self.strategy_callback(self.junction, self.goal)
        
        if new_road:
            assigned_lane = new_road.add_car(self)
            if assigned_lane is not None:
                self.road = new_road
                self.angle = new_road.angle
                self.lane_idx = assigned_lane
                self.visual_lane_offset = self.lane_idx - (self.road.n_lanes - 1) / 2.0
                return

        self.delete = True
        self.road = None

    def _pick_best_road(self) -> Road | None:
        """
        Greedy Best-First Search:
        Selects outgoing road with lowest Score = (Strategy Cost + Heuristic).
        """
        best_road = None
        min_score = float('inf')
        
        for road in self.junction.out_roads:
            if road._is_blocked:
                continue
            
            try:
                edge_cost = self.strategy_callback(road) or 0
            except:
                edge_cost = 0

            # 2. Heuristic: Euclidean Distance to Goal
            # We scale distance down (e.g. /100) so it balances with small integer weights like 'car count'
            dist_to_goal = road.end_pos.distance_to(self.goal.pos)
            heuristic = dist_to_goal / 100.0 
            
            score = edge_cost + heuristic
            
            if score < min_score:
                min_score = score
                best_road = road
                
        return best_road

    def _update_visual_pos(self):
        point_on_center_line = self.road.start_pos + (self.road.unit_vector * self.road_progress)
        target_offset = self.lane_idx - (self.road.n_lanes - 1) / 2.0
        self.visual_lane_offset += (target_offset - self.visual_lane_offset) * 0.1
        lane_offset_vec = self.road.perp_vector * (self.visual_lane_offset * self.road.lane_width)
        self.pos = point_on_center_line + lane_offset_vec

    def _safe_to_change_lanes(self, target_lane, target_speed, future_progress):
        """ 
        Checks if the target lane is free at the FUTURE position. 
        """
        
        if (target_lane == self.lane_idx) or (self.road.lanes_count[target_lane] + 1 >= self.road.lanes_count[self.lane_idx]):
            return False

        if not (20 < self.road_progress < self.road.length - 20):
               return False

        if self._dist_to_obstacle < 45:
            return False

        if np.isclose(0.0, target_speed, atol=0.1):
            return False

        buffer = 45.0 
        
        for car in self.road.cars:
            if car is self: continue
            if car.lane_idx != target_lane: continue

            dist_diff = car.road_progress - future_progress
            
            if abs(dist_diff) < buffer:
                return False
            
        return True

    @property
    def _dist_to_obstacle(self) -> float:
        """ 
        Calculates available space ahead, transparently looking across junctions.
        """
        closest_gap = 10000.0
        CAR_LENGTH = 25.0 
        
        for car in self.road.cars:
            if car is self: continue
            if car.lane_idx != self.lane_idx: continue

            if car.road_progress > self.road_progress:
                raw_dist = car.road_progress - self.road_progress
                gap = raw_dist - CAR_LENGTH
                if gap < closest_gap:
                    closest_gap = gap

        if self.road.end == self.goal:
            return closest_gap
        
        dist_to_end = self.road.length - self.road_progress
        
        if dist_to_end < closest_gap:
            
            if self.road.stopped:
                return max(0.0, dist_to_end)
            
            next_road = self.strategy_callback(self.junction, self.goal)

            
            if next_road:
                
                if next_road._is_blocked:
                    return closest_gap
                
                next_lane_space = next_road.get_space_at_start(next_road.best_lane)
                
                combined_gap = dist_to_end + next_lane_space
                
                if combined_gap < closest_gap:
                    closest_gap = combined_gap

        return max(0.0, closest_gap)