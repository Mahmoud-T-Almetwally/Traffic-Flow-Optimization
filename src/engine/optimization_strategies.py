from engine.components import Junction, Road


def least_accessed_road(junction: Junction, goal_junction: Junction) -> Road:
    """
    Picks the Least Accessed Road, i.e.
    Road 1, access times: 123
    Road 2, access times: 124
    Road 3, access times: 125

    this strategy would pick Road 1.
    """
    if not junction.out_roads:
        return None
    
    candidates = [road for road in junction.out_roads if road.can_reach(goal_junction)]

    if not candidates:
        return None
    
    return min(candidates, key=lambda r: r.access_times) 

def road_with_least_cars(junction: Junction, goal_junction: Junction) -> Road:
    """ 
    Picks the Road with the least car count, i.e.
    Road 1, car count = 1
    Road 2, car count = 5
    Road 3, car count = 4

    this strategy would pick Road 1.
    """
    if not junction.out_roads:
        return None
    
    candidates = [road for road in junction.out_roads if road.can_reach(goal_junction)]

    if not candidates:
        return None
    
    return min(candidates, key=lambda r: r.car_count)
    

def most_lanes_road(junction: Junction, goal_junction: Junction) -> Road:
    """ 
    Picks the Road with the most lane count, i.e.
    Road 1, lane count = 1
    Road 2, lane count = 5
    Road 3, lane count = 4
    
    this strategy would pick Road 2.
    """
    if not junction.out_roads:
        return None
    
    candidates = [road for road in junction.out_roads if road.can_reach(goal_junction)]

    if not candidates:
        return None
    
    return max(candidates, key=lambda r: r.n_lanes)
    

def highest_capacity_road(junction: Junction, goal_junction: Junction) -> Road:
    """ 
    Picks the Road with the highest car capacity, i.e.
    Road 1, car capacity = 1
    Road 2, car capacity = 5
    Road 3, car capacity = 4
    
    this strategy would pick Road 2.
    """
    if not junction.out_roads:
        return None
    
    candidates = [road for road in junction.out_roads if road.can_reach(goal_junction)]

    if not candidates:
        return None
    
    return max(candidates, key=lambda r: r.capacity)