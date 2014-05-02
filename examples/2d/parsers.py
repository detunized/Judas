@parsed_type("Point")
def parse_type_Point(value):
    return [int(value["x"]), int(value["y"])]

@parsed_type("Line")
def parse_type_Line(value):
    return [int(value["from"]["x"]), int(value["from"]["y"]), int(value["to"]["x"]), int(value["to"]["y"])]
