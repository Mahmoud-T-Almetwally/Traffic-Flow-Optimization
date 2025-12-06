from engine.components import Junction, Road

def least_accessed_road(junction: Junction) -> Road:
    """
    Picks the Least Accessed Road, i.e.
    Road 1, access times: 123
    Road 2, access times: 124
    Road 3, access times: 125

    this strategy would pick Road 1.
    """
    if not junction.out_roads:
        return None
    
    min_access = min(junction.access_times)
    idx = junction.access_times.index(min_access)
    
    # Increment the access counter for this road
    junction.access_times[idx] += 1
    
    return junction.out_roads[idx]

def road_with_least_cars(junction: Junction) -> Road:
    """ 
    Picks the Road with the least car count, i.e.
    Road 1, car count = 1
    Road 2, car count = 5
    Road 3, car count = 4

    this strategy would pick Road 1.
    """
    if not junction.out_roads:
        return None
    
    return min(junction.out_roads, key=lambda r: r.car_count)
    

def rotate_roads(junction: Junction) -> Road:
    """ 
    Picks the Road with the next index in the dictionary, i.e.
    Road 1, index = 0
    Road 2, index = 1
    Road 3, index = 2
    
    this strategy would pick Road 2 (assuming current index = 0).
    """
    if not junction.out_roads:
        return None
    
    current_idx = junction.current_road_idx
    road = junction.out_roads[current_idx]

    # Update index for next time (Modulo to loop back to 0)
    junction.current_road_idx = (current_idx + 1) % len(junction.out_roads)
    
    return road
    

def most_lanes_road(junction: Junction) -> Road:
    """ 
    Picks the Road with the most lane count, i.e.
    Road 1, lane count = 1
    Road 2, lane count = 5
    Road 3, lane count = 4
    
    this strategy would pick Road 2.
    """
    if not junction.out_roads:
        return None
    
    return max(junction.out_roads, key=lambda r: r.n_lanes)
    

def highest_capacity_road(junction: Junction) -> Road:
    """ 
    Picks the Road with the highest car capacity, i.e.
    Road 1, car capacity = 1
    Road 2, car capacity = 5
    Road 3, car capacity = 4
    
    this strategy would pick Road 2.
    """
    if not junction.out_roads:
        return None
    
    return max(junction.out_roads, key=lambda r: r.capacity)