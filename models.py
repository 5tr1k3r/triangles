import random
import time
from dataclasses import dataclass
from typing import Tuple, List, Set

import config as cfg

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
        self.triangle_values: List[List[int]] = []
        self.solution_line: List[Node] = []
        self.start = tuple(cfg.board_start)
        if cfg.board_exit is None:
            self.exit = (height, width)
        else:
            self.exit = tuple(cfg.board_exit)

        if self.start == self.exit:
            raise RuntimeError('start and exit should be different')

        if not (0 <= self.start[0] <= self.height and 0 <= self.start[1] <= self.width):
            raise RuntimeError('start is not within the board dimensions')

        if not (0 <= self.exit[0] <= self.height and 0 <= self.exit[1] <= self.width):
            raise RuntimeError('exit is not within the board dimensions')

        self.pg = None
        self.difficulty: int = 0

    def generate_paths(self):
        self.pg = PathGenerator(self.width, self.height, self.start, self.exit)
        self.pg.run()
        if not self.pg.paths:
            raise RuntimeError('no paths were generated')

    def get_solution_line(self):
        self.solution_line = self.pg.pick_random_path()

    def find_triangle_values(self):
        self.triangle_values = []
        for i in range(self.width):
            self.triangle_values.append([])

            for j in range(self.height):
                triangle_value = get_triangle_value(i, j, self.solution_line)
                # negative value means we're gonna hide this triangle
                if random.random() < cfg.hide_triangle_probability:
                    triangle_value *= -1
                self.triangle_values[i].append(triangle_value)

    def check_solution(self, line: List[Node]) -> bool:
        for i, row in enumerate(self.triangle_values):
            for j, triangle_value in enumerate(row):
                if triangle_value >= 1 and triangle_value != get_triangle_value(i, j, line):
                    return False

        return True

    def estimate_difficulty(self):
        if self.width < 2 or self.height < 2:
            self.difficulty = 0
            return

        score = 0
        triangles_count = len([x for row in self.triangle_values for x in row if x >= 1])
        concentration = triangles_count / (self.width * self.height)

        # divide the entire board in 2x2 blocks
        for i in range(self.width - 1):
            for j in range(self.height - 1):
                # too lazy to use numpy
                unfiltered_block = (self.triangle_values[i][j:j + 2] +
                                    self.triangle_values[i + 1][j:j + 2])
                block = [x for x in unfiltered_block if x >= 1]

                # 0 triangles - 1 score
                # 1 triangle  - 2 score
                # 2 triangles - 4 score
                # 3 triangles - 8 score
                # 4 triangles - 16 score
                score += 2 ** len(block)

        self.difficulty = score * self.get_concentration_difficulty_multiplier(concentration)

    @staticmethod
    def get_concentration_difficulty_multiplier(conc: float) -> float:
        # anything below or above the magic number will get lower multiplier
        magic_conc_number = 0.75
        if conc > magic_conc_number:
            delta = conc - magic_conc_number
            conc = magic_conc_number - delta

        return conc / magic_conc_number


class PathGenerator:
    def __init__(self, w: int, h: int, start: Node, end: Node):
        self.w = w
        self.h = h
        self.start = start
        self.end = end

        self.obstacles = self.add_obstacles(cfg.obstacles_count)
        self.paths: List[FullPath] = []

    def run(self):
        total_path_count = 0
        suitable_paths_count = 0
        min_len = self.w * self.h
        time_end = time.time() + cfg.generation_time_limit
        explored_all_paths = True

        for path in self.dfs_paths(self.start):
            total_path_count += 1

            if len(path) >= min_len:
                self.paths.append(path)
                suitable_paths_count += 1

            if suitable_paths_count >= cfg.max_paths_generated:
                explored_all_paths = False
                break

            if time.time() > time_end:
                print(f'time limit exceeded ({cfg.generation_time_limit}s)')
                explored_all_paths = False
                break

        gen_text = f'generated {suitable_paths_count} suitable paths'

        if explored_all_paths:
            print(f'total path count: {total_path_count}')
            print(f'{gen_text} ({(suitable_paths_count / total_path_count):.1%})')
        else:
            print(gen_text)

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


@dataclass
class PuzzleStats:
    time_spent: float
    difficulty: float


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
    pg_a.run()
    paths_a = set([''.join(f"{x}{y}" for x, y in path) for path in pg_a.paths])

    pg_b = PathGenerator(x, x, (0, 0), (x, x))
    pg_b.run()
    paths_b = set([''.join(f"{x}{y}" for x, y in path) for path in pg_b.paths])

    print(f'total path count {len(paths_a)}')
    if paths_a == paths_b:
        print('completely equal paths generated')
    else:
        print(f'there is {len(paths_a - paths_b)} paths A that dont exist in paths B')


if __name__ == '__main__':
    # board = Board(width=2, height=2)

    compare_generated_paths()
