import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

import arcade

import config as cfg
from config import window_width, window_height
from models import Board, Node, get_triangle_value

Coords = Tuple[float, float]


class TriangleText(arcade.Text):
    def __init__(self, num: int, x: int, y: int,
                 start_x: float, start_y: float):
        super().__init__(f'{num}', start_x, start_y, cfg.triangle_color,
                         font_size=cfg.triangle_text_size, anchor_x='center', anchor_y='center')

        self.num = num
        self.cell_x = x
        self.cell_y = y

        self.is_visible = True

        if num == 0 or random.random() < cfg.hide_triangle_probability:
            self.is_visible = False


@dataclass
class GExitData:
    rect_x: float
    rect_y: float
    rect_w: float
    rect_h: float
    circle_x: float
    circle_y: float
    circle_radius: float


class Triangles(arcade.Window):
    def __init__(self):
        super().__init__(window_width, window_height, 'Triangles', center_window=True)

        arcade.set_background_color(cfg.bg_color)
        self.board = Board(width=cfg.board_width, height=cfg.board_height)
        self.board.generate_paths()

        self.gboard_width = cfg.cell_size * self.board.width + cfg.lane_width * (self.board.width + 1)
        self.gboard_height = cfg.cell_size * self.board.height + cfg.lane_width * (self.board.height + 1)
        self.bottom_left_x = (window_width - self.gboard_width) / 2
        self.bottom_left_y = (window_height - self.gboard_height) / 2
        self.gcells = self.get_cell_coords()
        self.glines = self.get_lines_coords()
        self.exit_data = self.get_exit_data()

        self.triangle_texts: List[TriangleText] = []
        self.is_show_solution = False
        self.line: List[Node] = [self.board.start]
        self.is_solved = False
        self.is_validated_line = False

        self.start_new_puzzle()

    def start_new_puzzle(self):
        self.board.get_solution_line()
        self.board.find_triangle_values()
        self.triangle_texts = self.get_triangle_texts()

        self.is_show_solution = False
        self.line = [self.board.start]
        self.is_solved = False
        self.is_validated_line = False

    def on_draw(self):
        self.clear()

        self.draw_board()
        self.draw_triangles()
        self.draw_start()
        self.draw_exit()
        self.draw_line()
        self.draw_solution()

    def on_update(self, delta_time: float):
        self.check_validation()

    def check_validation(self):
        if self.line[-1] == self.board.exit:
            if not self.is_validated_line:
                self.is_solved = self.check_solution()
                self.is_validated_line = True
        elif self.is_validated_line:
            self.is_validated_line = False
            self.is_solved = False

            for triangle in [t for t in self.triangle_texts if t.is_visible]:
                triangle.color = cfg.triangle_color

    def check_solution(self) -> bool:
        success = True
        for triangle in [t for t in self.triangle_texts if t.is_visible]:
            if triangle.num != get_triangle_value(triangle.cell_x, triangle.cell_y, self.line):
                triangle.color = cfg.wrong_triangle_color
                success = False

        return success

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
        elif symbol == arcade.key.H:
            self.is_show_solution = not self.is_show_solution
        elif symbol == arcade.key.R:
            self.line = [self.board.start]
        elif symbol in (arcade.key.LEFT, arcade.key.UP, arcade.key.RIGHT, arcade.key.DOWN,
                        arcade.key.A, arcade.key.W, arcade.key.D, arcade.key.S):
            x, y = self.line[-1]

            if symbol in (arcade.key.LEFT, arcade.key.A):
                move = (x, y - 1)
            elif symbol in (arcade.key.UP, arcade.key.W):
                move = (x + 1, y)
            elif symbol in (arcade.key.RIGHT, arcade.key.D):
                move = (x, y + 1)
            elif symbol in (arcade.key.DOWN, arcade.key.S):
                move = (x - 1, y)

            # noinspection PyUnboundLocalVariable
            if self.is_reverting(move):
                self.line = self.line[:-1]
            elif self.is_valid_move(move):
                self.line += (move,)
        elif symbol == arcade.key.SPACE:
            self.start_new_puzzle()

    def is_reverting(self, move: Node) -> bool:
        return len(self.line) >= 2 and move == self.line[-2]

    def is_valid_move(self, move: Node) -> bool:
        x, y = move
        if not (0 <= x <= self.board.height and 0 <= y <= self.board.width):
            return False

        if move in self.line:
            return False

        return True

    def draw_board(self):
        arcade.draw_xywh_rectangle_filled(self.bottom_left_x, self.bottom_left_y,
                                          self.gboard_width, self.gboard_height,
                                          cfg.board_color)
        for row in self.gcells:
            for x, y in row:
                arcade.draw_xywh_rectangle_filled(x, y, cfg.cell_size, cfg.cell_size, cfg.cell_color)

    def draw_triangles(self):
        for triangle in self.triangle_texts:
            if triangle.is_visible:
                triangle.draw()

    def draw_start(self):
        self.draw_circle_at_position(self.board.start[1], self.board.start[0], cfg.board_color)

    def draw_exit(self):
        if self.exit_data:
            arcade.draw_xywh_rectangle_filled(self.exit_data.rect_x,
                                              self.exit_data.rect_y,
                                              self.exit_data.rect_w,
                                              self.exit_data.rect_h,
                                              cfg.board_color)
            arcade.draw_circle_filled(self.exit_data.circle_x,
                                      self.exit_data.circle_y,
                                      self.exit_data.circle_radius,
                                      cfg.board_color)
        else:
            # middle of the board
            self.draw_rectangle_at_position(self.board.exit[1], self.board.exit[0], cfg.board_color)

    def draw_circle_at_position(self, x: int, y: int, color: arcade.Color):
        start_x = self.bottom_left_x + cfg.lane_width / 2
        start_y = self.bottom_left_y + cfg.lane_width / 2
        arcade.draw_circle_filled(start_x + (x * (cfg.cell_size + cfg.lane_width)),
                                  start_y + (y * (cfg.cell_size + cfg.lane_width)),
                                  cfg.start_radius, color)

    def draw_rectangle_at_position(self, x: int, y: int, color: arcade.Color):
        start_x = self.bottom_left_x + cfg.lane_width / 2
        start_y = self.bottom_left_y + cfg.lane_width / 2
        arcade.draw_rectangle_filled(start_x + (x * (cfg.cell_size + cfg.lane_width)),
                                     start_y + (y * (cfg.cell_size + cfg.lane_width)),
                                     cfg.start_radius * 2, cfg.start_radius * 2, color)

    def draw_solution(self):
        if self.is_show_solution:
            arcade.draw_line_strip([self.glines[x][y] for x, y in self.board.solution_line],
                                   cfg.solution_color, line_width=cfg.player_line_width)

    def draw_line(self):
        color = cfg.solved_line_color if self.is_solved else cfg.line_color
        arcade.draw_line_strip([self.glines[x][y] for x, y in self.line],
                               color, line_width=cfg.player_line_width)

    def get_cell_coords(self) -> List[List[Coords]]:
        coords = []
        curr_y = self.bottom_left_y + cfg.lane_width
        for j in range(self.board.height):
            coords.append([])
            curr_x = self.bottom_left_x + cfg.lane_width

            for i in range(self.board.width):
                coords[j].append((curr_x, curr_y))
                curr_x += cfg.cell_size + cfg.lane_width

            curr_y += cfg.cell_size + cfg.lane_width

        return coords

    def get_lines_coords(self) -> List[List[Coords]]:
        coords = []
        curr_y = self.bottom_left_y + (cfg.lane_width / 2)
        for j in range(self.board.height + 1):
            coords.append([])
            curr_x = self.bottom_left_x + (cfg.lane_width / 2)

            for i in range(self.board.width + 1):
                coords[j].append((curr_x, curr_y))
                curr_x += cfg.cell_size + cfg.lane_width

            curr_y += cfg.cell_size + cfg.lane_width
        return coords

    def get_triangle_texts(self) -> List[TriangleText]:
        result = []
        for i, (row, grow) in enumerate(zip(self.board.cells, self.gcells)):
            for j, (cell, gcell) in enumerate(zip(row, grow)):
                x, y = gcell
                x += cfg.cell_size / 2
                y += cfg.cell_size / 2
                result.append(TriangleText(cell, i, j, x, y))

        return result

    def get_exit_data(self) -> Optional[GExitData]:
        x, y = self.board.exit
        dim_a = cfg.lane_width * 0.75
        dim_b = cfg.lane_width * 0.5
        offset_x = y * (cfg.cell_size + cfg.lane_width)
        offset_y = x * (cfg.cell_size + cfg.lane_width)

        # bottom or top
        if x in (0, self.board.height):
            rect_x = self.bottom_left_x
            circle_x = rect_x + dim_b

            if x == self.board.height:
                rect_y = self.bottom_left_y + self.gboard_height
                circle_y = rect_y + dim_a
            else:
                rect_y = self.bottom_left_y - dim_a
                circle_y = rect_y

            return GExitData(rect_x=rect_x + offset_x, rect_y=rect_y,
                             rect_w=cfg.lane_width, rect_h=dim_a,
                             circle_x=circle_x + offset_x, circle_y=circle_y,
                             circle_radius=dim_b)

        # left or right
        elif y in (0, self.board.width):
            rect_y = self.bottom_left_y
            circle_y = rect_y + dim_b

            if y == self.board.width:
                rect_x = self.bottom_left_x + self.gboard_width
                circle_x = rect_x + dim_a
            else:
                rect_x = self.bottom_left_x - dim_a
                circle_x = rect_x

            return GExitData(rect_x=rect_x, rect_y=rect_y + offset_y,
                             rect_w=dim_a, rect_h=cfg.lane_width,
                             circle_x=circle_x, circle_y=circle_y + offset_y,
                             circle_radius=dim_b)

        # middle of the board
        return


def main():
    Triangles()
    arcade.run()


if __name__ == '__main__':
    main()
