@parsed_type("int")
def parse_type_int(value):
    return [int(value)]

@parsed_type("const char *")
def parse_type_const_char_pointer(value):
    return [str(value)]
