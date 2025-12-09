import random
from engine.components import Point, Car, Road, Junction
from engine.optimization_strategies import (
    least_accessed_road, 
    most_lanes_road, 
    road_with_least_cars, 
    highest_capacity_road
)
from typing import Callable

class SimulationEngine:
    def __init__(self):
        self.junctions: dict[str, Junction] = {}
        self.roads: dict[str, Road] = {}
        self.cars: list[Car] = []
        
        self.strategies: dict[str, Callable[[Junction, Junction], Road]] = {
            "least_accessed_road": least_accessed_road,
            "road_with_least_cars": road_with_least_cars,
            "most_lanes_road": most_lanes_road,
            "highest_capacity_road": highest_capacity_road,
            "default": self.default_strategy
        }

        self.paused: bool = True
        self.simulation_speed_modifier: float = 1
        self.sim_elapsed_time: float = 0.0
        self.real_elapsed_time: float = 0.0

    def create_junction(self, x: float, y: float):
        pos = Point(x, y)
        junction_id = f"JUNC_{int(x)}_{int(y)}"
        
        if junction_id not in self.junctions:
            self.junctions[junction_id] = Junction(junction_id, pos)
        return junction_id

    def create_road(self, start_junc_id: str, end_junc_id: str, props: dict):
        start_junc = self.junctions.get(start_junc_id)
        end_junc = self.junctions.get(end_junc_id)
        
        if not start_junc or not end_junc:
            print(f"Error: Junctions {start_junc_id} or {end_junc_id} not found.")
            return

        road_id = f"ROAD_{start_junc_id}_TO_{end_junc_id}"
        
        if road_id in self.roads:
            return

        capacity = props.get('capacity', 10)
        lanes = props.get('lanes', 1)
        speed = props.get('speed', 50)
        blocked = props.get('blocked', False)

        new_road = Road(road_id, start_junc, end_junc, capacity, lanes, speed, blocked)
        
        start_junc.add_outgoing(new_road)
        end_junc.add_incoming(new_road)
        self.roads[road_id] = new_road

    def spawn_car(self, spawn_junction_id: str, goal: Junction | str = "random", strategy_name: str = "default"):
        if spawn_junction_id not in self.junctions:
            return
        
        if goal == "random":
            junctions = [junc for junc in self.junctions.values() if junc.id != spawn_junction_id]
            goal = random.choice(junctions)
        
        strategy_fn = self.strategies.get(strategy_name, self.default_strategy)
        new_car = Car(f"Car-{len(self.cars)}", self.junctions[spawn_junction_id], goal, strategy_fn)
        
        new_car.resolve_junction()
        
        if new_car.road:
            self.cars.append(new_car)

    def default_strategy(self, junction: Junction, goal: Junction) -> Road | None:
        """ Picks a random available road """
        available_roads = [r for r in junction.out_roads if r.available]
        
        if not available_roads:
            return None
        
        candidates = [road for road in junction.out_roads if road.can_reach(goal)]

        if not candidates:
            return None

        return random.choice(candidates)
    
    def start(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def set_simulation_speed(self, value: float):
        self.simulation_speed_modifier = value

    def set_optimization_strategy(self, strategy_name):
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            for car in self.cars:
                car.strategy_callback = strategy

    def update(self, dt=0.033):
        if not self.paused:
            self.real_elapsed_time += dt
            elapsed = dt * self.simulation_speed_modifier
            self.sim_elapsed_time += elapsed
            for road in self.roads.values():
                road.update_lights(elapsed)

            self.cars.sort(key=lambda c: (c.road.id, c.lane_idx, -c.road_progress))

            for car in self.cars:
                if not car.delete:
                    car.move(elapsed)

            active_cars = []
            for car in self.cars:
                if car.delete:
                    if car.road:
                        car.road.remove_car(car.id)
                        car.road.change_lane_count(car.lane_idx, -1)
                else:
                    active_cars.append(car)
            
            self.cars = active_cars