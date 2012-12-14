def parse_type_LatLon(value):
    return [float(value["lat"]), float(value["lon"])]

def parse_type_Polyline(value):
    points = value["points"]["_M_impl"]
    start = points["_M_start"]
    size = int(points["_M_finish"] - start)
    return [coord for i in range(size) for coord in parse_type_LatLon(start[i])]
