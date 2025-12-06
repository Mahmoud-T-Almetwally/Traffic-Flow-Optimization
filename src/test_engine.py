import unittest
import math
from engine.components import Point, Junction, Road, Car
from engine.simulation_engine import SimulationEngine
from engine.optimization_strategies import least_accessed_road, road_with_least_cars

class TestTrafficEngine(unittest.TestCase):

    def setUp(self):
        """Set up a fresh engine before every test."""
        self.engine = SimulationEngine()

    # ==========================================
    # 1. MATH & GEOMETRY TESTS
    # ==========================================

    def test_point_math(self):
        """Verify vector arithmetic is correct."""
        p1 = Point(10, 10)
        p2 = Point(20, 20)
        
        # Test Distance
        dist = p1.distance_to(p2)
        expected_dist = math.hypot(10, 10)
        self.assertAlmostEqual(dist, expected_dist, places=5, msg="Distance calc failed")

        # Test Addition
        p3 = p1 + p2
        self.assertEqual((p3.x, p3.y), (30, 30), "Vector addition failed")

        # Test Scalar Multiplication
        p4 = p1 * 2
        self.assertEqual((p4.x, p4.y), (20, 20), "Scalar multiplication failed")

    def test_road_geometry(self):
        """Verify road vectors and lane offsets."""
        start = Junction("A", Point(0, 0))
        end = Junction("B", Point(100, 0)) # Horizontal road
        
        # 2 Lanes, Lane Width = 20
        road = Road("R1", start, end, capacity=10, lanes=2, speed=10, blocked=False)
        
        # Check Unit Vector (Should be 1, 0)
        self.assertAlmostEqual(road.unit_vector.x, 1.0)
        self.assertAlmostEqual(road.unit_vector.y, 0.0)

        # Check Perp Vector (Should be 0, 1 for 90deg rotation or 0, -1)
        # Based on your code: (-y, x) -> (-0, 1) -> (0, 1)
        self.assertAlmostEqual(road.perp_vector.x, 0.0)
        self.assertAlmostEqual(road.perp_vector.y, 1.0)

        # Check Lane Offsets
        # Lane 0: Index 0. Scale = 0 - (2-1)/2 = -0.5. Offset = -0.5 * 20 = -10
        # Lane 1: Index 1. Scale = 1 - (2-1)/2 = +0.5. Offset = +0.5 * 20 = +10
        pos_l0 = road.get_lane_start_offset(0)
        pos_l1 = road.get_lane_start_offset(1)

        self.assertEqual(pos_l0.y, -10, "Lane 0 offset incorrect")
        self.assertEqual(pos_l1.y, 10, "Lane 1 offset incorrect")

    # ==========================================
    # 2. MOVEMENT & PHYSICS TESTS
    # ==========================================

    def test_car_movement_integration(self):
        """Verify car moves actual distance over time."""
        # Create A -> B
        self.engine.create_junction(0, 0) # id JUNC_0_0
        self.engine.create_junction(100, 0) # id JUNC_100_0
        
        self.engine.create_road("JUNC_0_0", "JUNC_100_0", {"speed": 50, "lanes": 1})
        
        self.engine.spawn_car("JUNC_0_0")
        car = self.engine.cars[0]
        
        # Update for 1 second
        dt = 1.0
        self.engine.update(dt)
        
        # Expected: Start(0,0) + Speed(50)*Time(1) = 50
        # Note: Lane offset might affect Y, but X should be exactly 50 if horizontal
        self.assertAlmostEqual(car.road_progress, 50.0, msg="Car progress calculation wrong")
        self.assertAlmostEqual(car.pos.x, 50.0, delta=0.1, msg="Car visual X position wrong")

    def test_dead_end_removal(self):
        """Verify cars are removed when they run out of road."""
        self.engine.create_junction(0, 0)
        self.engine.create_junction(10, 0) # Short road
        self.engine.create_road("JUNC_0_0", "JUNC_10_0", {"speed": 20}) # Length 10
        
        self.engine.spawn_car("JUNC_0_0")
        
        # Move 1 second (travels 20 units, road is 10) -> Should finish
        self.engine.update(1.0)
        
        self.assertEqual(len(self.engine.cars), 0, "Car was not garbage collected at dead end")

    # ==========================================
    # 3. LOGIC & STRATEGY TESTS
    # ==========================================

    def test_junction_handover(self):
        """Verify car jumps from Road A to Road B correctly and preserves momentum."""
        # Setup: A(0,0) -> B(100,0) -> C(200,0)
        self.engine.create_junction(0, 0)
        self.engine.create_junction(100, 0)
        self.engine.create_junction(200, 0)
        
        # Road 1: Length 100, Speed 100
        self.engine.create_road("JUNC_0_0", "JUNC_100_0", {"speed": 100}) 
        # Road 2: Length 100, Speed 100
        self.engine.create_road("JUNC_100_0", "JUNC_200_0", {"speed": 100}) 
        
        self.engine.spawn_car("JUNC_0_0")
        car = self.engine.cars[0]
        
        # Action: Move 1.1 seconds @ 100 speed = 110 units distance.
        # Road 1 is only 100 units long.
        self.engine.update(1.1)
        
        # Check 1: Did we switch roads?
        self.assertIsNotNone(car.road)
        # The new road starts at x=100
        self.assertEqual(car.road.start_pos.x, 100, "Car did not transition to second road")
        
        # Check 2: Overshoot / Momentum Handling (Updated Logic)
        # Old Logic expected 0. New Logic expects the remainder (10 units).
        # Calculation: (1.1s * 100 speed) - 100 road_length = 10 units excess.
        self.assertAlmostEqual(car.road_progress, 10.0, places=1, msg="Car lost momentum (progress should carry over)")
        
        # Check 3: Absolute Visual Position
        # The car should be at World X = 110 (100 start of road + 10 progress)
        self.assertAlmostEqual(car.pos.x, 110.0, places=1, msg="Car visual position incorrect after handover")

    def test_strategy_least_cars(self):
        """Verify car picks the empty road over the busy road."""
        #     /-- Road 1 (Has 5 cars) --\
        # Start                          End
        #     \-- Road 2 (Empty)      --/
        
        start = self.engine.create_junction(0, 0)
        end = self.engine.create_junction(100, 0)
        
        # Create manually to populate easier
        start_node = self.engine.junctions[start]
        end_node = self.engine.junctions[end]
        
        r1 = Road("R1", start_node, end_node, 20, 1, 50, False)
        r2 = Road("R2", start_node, end_node, 20, 1, 50, False)
        
        start_node.add_outgoing(r1)
        start_node.add_outgoing(r2)
        
        # Artificially fill Road 1
        r1.lanes_count[0] = 5
        r2.lanes_count[0] = 0
        
        # Test Strategy
        chosen_road = road_with_least_cars(start_node)
        self.assertEqual(chosen_road.id, "R2", "Strategy did not pick the empty road")

    def test_lane_change_logic(self):
        """Verify car switches lane counts correctly."""
        start = Junction("A", Point(0,0))
        end = Junction("B", Point(100,0))
        road = Road("R1", start, end, capacity=10, lanes=2, speed=50, blocked=False)
        
        # Fill Lane 0 completely
        road.lanes_count[0] = 5 # Capacity is 10/2 = 5 per lane. Lane 0 is FULL.
        road.lanes_count[1] = 0 # Empty
        
        car = Car(start, lambda j: road)
        car.road = road
        car.lane_idx = 0 # Force car onto full lane
        
        # Manually trigger move logic step (simulating update)
        # We need to simulate the car logic inside move() regarding lane change
        
        # The car code checks: if best_lane != current_lane: change.
        # best_lane property returns index of MIN count.
        # Lane 0 has 5, Lane 1 has 0. Min is Lane 1.
        
        self.assertEqual(road.best_lane, 1)
        
        # Execute Move
        car.move(0.1)
        
        self.assertEqual(car.lane_idx, 1, "Car failed to switch to the empty lane")
        self.assertEqual(road.lanes_count[0], 4, "Old lane count not decremented")
        self.assertEqual(road.lanes_count[1], 1, "New lane count not incremented")

if __name__ == '__main__':
    unittest.main()