import base64


def bear64encode(data):
    return base64.b64encode(data).decode().replace("/", "_").replace("+", "🐻").rstrip("=")


def bear64decode(data):
    return base64.b64decode(data.replace("_", "/").replace("🐻", "+") + "==")


def get_direction(a, b):
    return {(0, 1): "00", (0, -1): "01", (1, 0): "10", (-1, 0): "11"}[(b[0] - a[0], b[1] - a[1])]


def apply_direction(a, d):
    d = {"00": (0, 1), "01": (0, -1), "10": (1, 0), "11": (-1, 0)}[d]
    return a[0] + d[0], a[1] + d[1]


def wind_cw(pd):
    a = ["00", "10", "01", "11"]
    return a[(a.index(pd) + 1) % 4]


def wind_ccw(pd):
    a = ["00", "10", "01", "11"]
    return a[(a.index(pd) + 3) % 4]


def encode_relative(d1, d2):
    if d2 == d1:
        return "0"
    if wind_cw(d1) == d2:
        return "10"
    elif wind_ccw(d1) == d2:
        return "11"


def decode_relative(bs, pos, pd):
    if bs[pos] == "0":
        return pos + 1, pd
    pos += 1
    if bs[pos] == "0":
        return pos + 1, wind_cw(pd)
    else:
        return pos + 1, wind_ccw(pd)


def encode_default(data, default):
    if data == default:
        return "0"

    return "1" + bin(data[0])[2:].zfill(3) + bin(data[1])[2:].zfill(3)


def decode_default(bs, pos, default):
    if bs[pos] == "0":
        return pos + 1, default

    return pos + 7, (int(bs[pos + 1:pos + 4], 2), int(bs[pos + 4:pos + 7], 2))


def get_triangle_value(i, j, all_sublines):
    prev_corner = (i, j)
    d = "10"
    all_possible_neighbor_lines = set()
    for _ in range(4):
        corner = apply_direction(prev_corner, d)
        all_possible_neighbor_lines |= {(prev_corner, corner), (corner, prev_corner)}
        d = wind_ccw(d)
        prev_corner = corner

    return len(all_possible_neighbor_lines & all_sublines)


def ponchik_encode(width, height, start, exit_, triangle_values, solution_line):
    # todo add support up to 15x15
    assert width <= 7 and height <= 7
    assert solution_line[0] == start
    assert solution_line[-1] == exit_

    bs = bin(width)[2:].zfill(3) + bin(height)[2:].zfill(3)
    bs += encode_default(start, (0, 0)) + encode_default(exit_, (height, width))

    all_sublines = {(x, y) for x, y in zip(solution_line[:-1], solution_line[1:])}

    for i in range(height):
        for j in range(width):
            computed = get_triangle_value(i, j, all_sublines)
            if computed == triangle_values[i * width + j]:
                bs += "0"
            elif triangle_values[i * width + j] == 0:
                bs += "1"
            else:
                assert False

    prev_d = get_direction(solution_line[0], solution_line[1])
    bs += prev_d

    for i in range(2, len(solution_line) - 1):
        d = get_direction(solution_line[i - 1], solution_line[i])
        bs += encode_relative(prev_d, d)
        prev_d = d

    pad = (len(bs) + 3) % 8
    bs += "0" * ((8 - pad) % 8) + bin(pad)[2:].zfill(3)
    return base64.b64encode(bytes([int(bs[i:i + 8], 2) for i in range(0, len(bs), 8)]))


def ponchik_decode(data):
    bs = "".join(bin(b)[2:].zfill(8) for b in base64.b64decode(data))
    bs = bs[:-3 - (8 - int(bs[-3:], 2)) % 8]
    width = int(bs[:3], 2)
    height = int(bs[3:6], 2)
    pos, start = decode_default(bs, 6, (0, 0))
    pos, exit_ = decode_default(bs, pos, (height, width))

    triangle_pos = pos
    pos = triangle_pos + width * height

    prev_d = bs[pos:pos + 2]
    solution_line = [start, apply_direction(start, prev_d)]

    pos += 2
    while pos < len(bs):
        pos, prev_d = decode_relative(bs, pos, prev_d)
        solution_line.append(apply_direction(solution_line[-1], prev_d))
    solution_line.append(exit_)

    all_sublines = {(x, y) for x, y in zip(solution_line[:-1], solution_line[1:])}

    triangle_values = []
    for i in range(height):
        for j in range(width):
            computed = get_triangle_value(i, j, all_sublines)
            triangle_values.append(computed if bs[triangle_pos + i * width + j] == "0" else -computed)

    return width, height, start, exit_, triangle_values, solution_line
