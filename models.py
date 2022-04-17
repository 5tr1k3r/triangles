import random
import time
from typing import Tuple, List, Set

import config as cfg
from utils import timeit

Node = Tuple[int, int]
FullPath = List[Node]


def get_triangle_value(i: int, j: int, line: FullPath) -> int:
    all_sublines = [(x, y) for x, y in zip(line[:-1], line[1:])]
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


class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[int]] = []
        self.solution_line: List[Node] = []
        self.start = tuple(cfg.board_start)
        if cfg.board_exit is None:
            self.exit = (height, width)
        else:
            self.exit = tuple(cfg.board_exit)

        if self.start == self.exit:
            raise RuntimeError('start and exit should be different')

    def generate_line(self):
        pg = PathGenerator(self.width, self.height, self.start, self.exit)
        pg.generate_paths()
        if not pg.paths:
            raise RuntimeError('no paths were generated')

        self.solution_line = pg.pick_random_path()

    def get_all_paths(self):
        pass

    def find_triangle_values(self):
        for i in range(self.width):
            self.cells.append([])

            for j in range(self.height):
                self.cells[i].append(get_triangle_value(i, j, self.solution_line))


class PathGenerator:
    def __init__(self, w: int, h: int, start: Node, end: Node):
        self.w = w
        self.h = h
        self.start = start
        self.end = end

        self.obstacles = self.add_obstacles(0)
        self.paths: List[FullPath] = []

    @timeit
    def generate_paths(self):
        suitable_paths_count = 0
        min_len = self.w * self.h
        time_end = time.time() + cfg.generation_time_limit

        for path in self.dfs_paths(self.start):
            if len(path) >= min_len:
                self.paths.append(path)
                suitable_paths_count += 1

            if suitable_paths_count >= cfg.max_paths_generated:
                print(f'generated {suitable_paths_count} paths')
                break

            if time.time() > time_end:
                print(f'time limit exceeded ({cfg.generation_time_limit}s), '
                      f'generated {suitable_paths_count} paths')
                break

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

    def get_candidates(self, start: Node, path: FullPath) -> List[Node]:
        result = list(self.get_neighbors(start) - set(path) - self.obstacles)
        random.shuffle(result)
        return result

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

    def pick_random_path(self):
        return random.choice(self.paths)


def test_obstacles():
    n = 100
    total_path_count = 0

    for i in range(n):
        size = 4
        generator = PathGenerator(size, size, (0, 0), (size, size))

        total_path_count += len(generator.paths)

    print(total_path_count / n)


def compare_generated_paths():
    x = 7
    pg_a = PathGenerator(x, x, (0, 0), (x, x))
    pg_a.generate_paths()
    paths_a = set([''.join(f"{x}{y}" for x, y in path) for path in pg_a.paths])

    pg_b = PathGenerator(x, x, (0, 0), (x, x))
    pg_b.generate_paths()
    paths_b = set([''.join(f"{x}{y}" for x, y in path) for path in pg_b.paths])

    print(f'total path count {len(paths_a)}')
    if paths_a == paths_b:
        print('completely equal paths generated')
    else:
        print(f'there is {len(paths_a - paths_b)} paths A that dont exist in paths B')


if __name__ == '__main__':
    # board = Board(width=2, height=2)

    compare_generated_paths()
