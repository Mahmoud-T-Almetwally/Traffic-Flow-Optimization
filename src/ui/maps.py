from engine.simulation_engine import SimulationEngine

class MapLoader:
    @staticmethod
    def load_map(engine: SimulationEngine, map_name: str):
        """ Clears and populates the engine based on map_name """
        
        # --- Standard Properties ---
        # High speed, High capacity
        p_highway = {"capacity": 40, "speed": 100, "lanes": 2} 
        # Medium speed, medium capacity
        p_main = {"capacity": 15, "speed": 60, "lanes": 2}
        # Low speed, low capacity (Bottlenecks)
        p_street = {"capacity": 8, "speed": 30, "lanes": 1}

        if map_name == "The Grid (Pathfinding Test)":
            # A 4x3 Grid of alternating one-way streets.
            # Good for testing if cars can find their way around blocked roads.
            
            rows = 3
            cols = 4
            spacing_x = 250
            spacing_y = 200
            offset_x = 100
            offset_y = 100

            junctions = {}

            # 1. Create Grid of Junctions
            for r in range(rows):
                for c in range(cols):
                    jid = engine.create_junction(offset_x + c * spacing_x, offset_y + r * spacing_y)
                    junctions[(r, c)] = jid

            # 2. Horizontal Roads (Alternating Directions)
            for r in range(rows):
                for c in range(cols - 1):
                    start = junctions[(r, c)]
                    end = junctions[(r, c+1)]
                    
                    # Even rows go East, Odd rows go West
                    if r % 2 == 0:
                        engine.create_road(start, end, p_main)
                    else:
                        engine.create_road(end, start, p_main)

            # 3. Vertical Roads (Alternating Directions)
            for c in range(cols):
                for r in range(rows - 1):
                    start = junctions[(r, c)]
                    end = junctions[(r+1, c)]
                    
                    # Even cols go South, Odd cols go North
                    if c % 2 == 0:
                        engine.create_road(start, end, p_street)
                    else:
                        engine.create_road(end, start, p_street)

        elif map_name == "Highway with Bypass":
            # Tests Optimization Strategies:
            # Route A: Short, Direct, but LOW Capacity (Traffic Jam prone)
            # Route B: Long, Indirect, but HIGH Speed/Capacity (Bypass)
            
            # Start and End
            start_node = engine.create_junction(50, 300)
            end_node = engine.create_junction(950, 300)

            # --- Route A: The City Center (Direct but slow) ---
            c1 = engine.create_junction(300, 300)
            c2 = engine.create_junction(700, 300)
            
            engine.create_road(start_node, c1, p_main)
            # This is the bottleneck: 1 lane, low capacity
            engine.create_road(c1, c2, {"capacity": 5, "speed": 40, "lanes": 1}) 
            engine.create_road(c2, end_node, p_main)

            # --- Route B: The Highway Bypass (Long but fast) ---
            h1 = engine.create_junction(200, 100)
            h2 = engine.create_junction(500, 50) # Way up top
            h3 = engine.create_junction(800, 100)

            # Connect Start -> Bypass
            engine.create_road(start_node, h1, p_highway)
            engine.create_road(h1, h2, p_highway)
            engine.create_road(h2, h3, p_highway)
            engine.create_road(h3, end_node, p_highway)

        elif map_name == "Dual Carriageway Loop":
            # Physically separated lanes to prevent ANY overlap.
            # Two concentric rings acting as a two-way highway.

            # Inner Ring (Clockwise)
            i_tl = engine.create_junction(200, 150) # Top Left
            i_tr = engine.create_junction(800, 150) # Top Right
            i_br = engine.create_junction(800, 450) # Bottom Right
            i_bl = engine.create_junction(200, 450) # Bottom Left

            engine.create_road(i_tl, i_tr, p_highway)
            engine.create_road(i_tr, i_br, p_highway)
            engine.create_road(i_br, i_bl, p_highway)
            engine.create_road(i_bl, i_tl, p_highway)

            # Outer Ring (Counter-Clockwise)
            # Offset by 50px so they don't touch
            o_tl = engine.create_junction(150, 100)
            o_tr = engine.create_junction(850, 100)
            o_br = engine.create_junction(850, 500)
            o_bl = engine.create_junction(150, 500)

            engine.create_road(o_tr, o_tl, p_highway) # Note direction reversed
            engine.create_road(o_tl, o_bl, p_highway)
            engine.create_road(o_bl, o_br, p_highway)
            engine.create_road(o_br, o_tr, p_highway)

            # Bridges (Connecting Inner and Outer to allow looping back)
            # Bridge Top
            engine.create_road(o_tr, i_tr, p_street)
            # Bridge Bottom
            engine.create_road(i_bl, o_bl, p_street)