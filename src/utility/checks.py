

def CHK_type(value, type):
    return value = type(value)


def is_float(value):
    return CHK_type(value, float)


def is_int(value):
    return CHK_type(value, int)


def is_str(value):
    return CHK_type(value, str)
