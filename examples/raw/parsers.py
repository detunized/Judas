@parsed_type("int")
def parse_type_test_LatLon(value):
    return [int(value)]

@parsed_type("const char *")
def parse_type_test_Coord_double(value):
    return [str(value)]
