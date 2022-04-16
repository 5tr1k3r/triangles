import random
from typing import List, Tuple

import arcade

import config as cfg
from config import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE
from models import Board, Node

Coords = Tuple[float, float]


class TriangleText(arcade.Text):
    def __init__(self, value: int, start_x: float, start_y: float):
        super().__init__(f'{value}', start_x, start_y, cfg.triangle_color,
                         font_size=16, anchor_x='center', anchor_y='center')

        self.is_visible = True

        if value == 0:
            self.is_visible = False
        elif random.random() < cfg.hide_triangle_probability:
            self.is_visible = False


class Triangles(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, center_window=True)

        arcade.set_background_color(cfg.bg_color)
        self.board = Board(width=4, height=4)
        self.board.generate_line()
        self.board.find_triangle_values()

        self.gboard_width = cfg.cell_size * self.board.width + cfg.line_width * (self.board.width + 1)
        self.gboard_height = cfg.cell_size * self.board.height + cfg.line_width * (self.board.height + 1)
        self.bottom_left_x = (WINDOW_WIDTH - self.gboard_width) / 2
        self.bottom_left_y = (WINDOW_HEIGHT - self.gboard_height) / 2
        self.gcells = self.get_cell_coords()
        self.glines = self.get_lines_coords()
        self.triangle_texts = self.get_triangle_texts()

        self.is_show_solution = False
        self.line: List[Node] = [self.board.start]

    def on_draw(self):
        self.clear()

        self.draw_board()
        self.draw_triangles()
        self.draw_start_end()
        self.draw_line()
        self.draw_solution()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
        elif symbol == arcade.key.H:
            self.is_show_solution = not self.is_show_solution
        elif symbol in (arcade.key.LEFT, arcade.key.UP, arcade.key.RIGHT, arcade.key.DOWN):
            x, y = self.line[-1]

            if symbol == arcade.key.LEFT:
                move = (x, y - 1)
            elif symbol == arcade.key.UP:
                move = (x + 1, y)
            elif symbol == arcade.key.RIGHT:
                move = (x, y + 1)
            elif symbol == arcade.key.DOWN:
                move = (x - 1, y)

            # noinspection PyUnboundLocalVariable
            if self.is_reverting(move):
                self.line = self.line[:-1]
            elif self.is_valid_move(move):
                self.line += (move, )

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

    def draw_start_end(self):
        # todo support custom end
        start_x = self.bottom_left_x + cfg.line_width / 2
        start_y = self.bottom_left_y + cfg.line_width / 2
        arcade.draw_circle_filled(start_x + (self.board.start[0] * (cfg.cell_size + cfg.line_width)),
                                  start_y + (self.board.start[1] * (cfg.cell_size + cfg.line_width)),
                                  cfg.start_radius, cfg.board_color)

        top_right_x = self.bottom_left_x + self.gboard_width
        top_right_y = self.bottom_left_y + self.gboard_height
        arcade.draw_xywh_rectangle_filled(top_right_x - cfg.line_width,
                                          top_right_y,
                                          cfg.line_width, cfg.line_width * 0.75,
                                          cfg.board_color)
        arcade.draw_circle_filled(top_right_x - cfg.line_width * 0.5,
                                  top_right_y + cfg.line_width * 0.75,
                                  cfg.line_width * 0.5,
                                  cfg.board_color)

    def draw_solution(self):
        if self.is_show_solution:
            arcade.draw_line_strip([self.glines[x][y] for x, y in self.board.solution_line],
                                   cfg.solution_color, line_width=10)

    def draw_line(self):
        arcade.draw_line_strip([self.glines[x][y] for x, y in self.line],
                               cfg.line_color, line_width=10)

    def get_cell_coords(self) -> List[List[Coords]]:
        coords = []
        curr_y = self.bottom_left_y + cfg.line_width
        for j in range(self.board.height):
            coords.append([])
            curr_x = self.bottom_left_x + cfg.line_width

            for i in range(self.board.width):
                coords[j].append((curr_x, curr_y))
                curr_x += cfg.cell_size + cfg.line_width

            curr_y += cfg.cell_size + cfg.line_width

        return coords

    def get_lines_coords(self) -> List[List[Coords]]:
        coords = []
        curr_y = self.bottom_left_y + (cfg.line_width / 2)
        for j in range(self.board.height + 1):
            coords.append([])
            curr_x = self.bottom_left_x + (cfg.line_width / 2)

            for i in range(self.board.width + 1):
                coords[j].append((curr_x, curr_y))
                curr_x += cfg.cell_size + cfg.line_width

            curr_y += cfg.cell_size + cfg.line_width
        return coords

    def get_triangle_texts(self) -> List[TriangleText]:
        result = []
        for row, grow in zip(self.board.cells, self.gcells):
            for cell, gcell in zip(row, grow):
                x, y = gcell
                x += cfg.cell_size / 2
                y += cfg.cell_size / 2
                result.append(TriangleText(cell, x, y))

        return result


def main():
    Triangles()
    arcade.run()


if __name__ == '__main__':
    main()
