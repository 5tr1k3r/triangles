import random
from typing import Tuple, List, Set

# from utils import timeit

Node = Tuple[int, int]
FullPath = List[Node]


class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[int]] = []
        self.line: List[Node] = []
        self.start = (0, 0)
        self.end = (width, height)

    def generate_line(self):
        y, x = self.end
        pg = PathGenerator(self.width, self.height, self.start, (x, y))
        pg.generate_paths()
        self.line = pg.pick_random_path(min_len=self.width * self.height)

    def get_all_paths(self):
        pass

    def find_triangle_values(self):
        for i in range(self.width):
            self.cells.append([])

            for j in range(self.height):
                self.cells[i].append(self.get_triangle_value(i, j))

    def get_triangle_value(self, i: int, j: int) -> int:
        all_sublines = [(x, y) for x, y in zip(self.line[:-1], self.line[1:])]
        corner_sw = (i, j)
        corner_nw = (i + 1, j)
        corner_ne = (i + 1, j + 1)
        corner_se = (i, j + 1)
        all_possible_neighbor_lines = {(corner_sw, corner_nw),
                                       (corner_nw, corner_sw),
                                       (corner_nw, corner_ne),
                                       (corner_ne, corner_nw),
                                       (corner_ne, corner_se),
                                       (corner_se, corner_ne),
                                       (corner_se, corner_sw),
                                       (corner_sw, corner_se)}

        return len(all_possible_neighbor_lines.intersection(set(all_sublines)))


class PathGenerator:
    def __init__(self, w: int, h: int, start: Node, end: Node):
        self.w = w
        self.h = h
        self.start = start
        self.end = end

        self.obstacles = self.add_obstacles(0)
        self.paths: List[FullPath] = []

    # @timeit
    def generate_paths(self):
        self.paths = [p for p in self.dfs_paths(self.start)]

    def dfs_paths(self, start: Node, path=None):
        if path is None:
            path = [start]
        if path[-1] == self.end:
            yield path
            return
        for field in self.get_candidates(start, path):
            yield from self.dfs_paths(field, path + [field])

    def get_neighbors(self, node: Node) -> Set[Node]:
        x, y = node
        all_neighbors = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]

        return {(x, y) for x, y in all_neighbors if 0 <= x <= self.h and 0 <= y <= self.w}

    def get_candidates(self, start: Node, path: FullPath) -> Set[Node]:
        return self.get_neighbors(start) - set(path) - self.obstacles

    def display_paths(self):
        if len(self.paths) == 0:
            print('no paths at all')
            return

        total_path_length = 0
        max_len = 0
        min_len = float('inf')

        # for p in sorted(self.paths, key=len):
        #     print(len(p), p)

        for p in self.paths:
            total_path_length += len(p)
            if len(p) > max_len:
                max_len = len(p)

            if len(p) < min_len:
                min_len = len(p)

        print(f'total count {len(self.paths)}, longest path {max_len}, '
              f'avg path {(total_path_length / len(self.paths)):.1f}, '
              f'shortest path {min_len}')

    def add_obstacles(self, n: int) -> Set[Node]:
        result = set()
        for i in range(n):
            result.add((random.randint(0, self.h - 1), random.randint(0, self.w - 1)))

        return result

    def pick_random_path(self, min_len: int):
        return random.choice([p for p in self.paths if len(p) >= min_len])


def test_obstacles():
    n = 100
    total_path_count = 0

    for i in range(n):
        size = 4
        generator = PathGenerator(size, size, (0, 0), (size, size))

        total_path_count += len(generator.paths)

    print(total_path_count / n)


if __name__ == '__main__':
    # board = Board(width=2, height=2)

    s = 4
    g = PathGenerator(2, 4, (0, 0), (4, 2))
    g.generate_paths()
    g.display_paths()
