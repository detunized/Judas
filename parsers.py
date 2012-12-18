# TODO: Move this out of here
def parsed_type(name):
    def parsed_type_decorator(function):
        function.parsed_type = name
        return function
    return parsed_type_decorator

@parsed_type("test::LatLon")
def parse_type_test_LatLon(value):
    return [float(value["lat"]), float(value["lon"])]

@parsed_type("test::Coord<double>")
def parse_type_test_Coord_double(value):
    return [float(value["lat"]), float(value["lon"])]

@parsed_type("test::Polyline")
def parse_type_test_Polyline(value):
    points = value["points"]["_M_impl"]
    start = points["_M_start"]
    size = int(points["_M_finish"] - start)
    return [coord for i in range(size) for coord in parse_type_test_LatLon(start[i])]

# Aliases
parse_type_test_DoubleCoord = parse_type_test_Coord_double
