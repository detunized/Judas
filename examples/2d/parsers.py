@parsed_type("Point")
def parse_type_Point(value):
    return [int(value["x"]), int(value["y"])]

@parsed_type("Line")
def parse_type_Line(value):
    return [parse_type_Point(value["from"]), parse_type_Point(value["to"])]
