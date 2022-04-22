from dataclasses import dataclass
from typing import Tuple, List, Optional

import arcade

import config as cfg
from models import Board, Node, get_triangle_value

Coords = Tuple[float, float]


class TriangleText(arcade.Text):
    def __init__(self, num: int, x: int, y: int,
                 start_x: float, start_y: float):
        super().__init__(f'{num}', start_x, start_y, cfg.triangle_color[cfg.theme],
                         font_size=cfg.triangle_text_size, anchor_x='center', anchor_y='center')

        self.num = num
        self.cell_x = x
        self.cell_y = y


@dataclass
class GExitData:
    rect_x: float
    rect_y: float
    rect_w: float
    rect_h: float
    circle_x: float
    circle_y: float
    circle_radius: float


class GameDrawing:
    def __init__(self, board: Board):
        self.board = board
        self.gboard_width = cfg.cell_size * self.board.width + cfg.lane_width * (self.board.width + 1)
        self.gboard_height = cfg.cell_size * self.board.height + cfg.lane_width * (self.board.height + 1)
        self.bottom_left_x = (cfg.window_width - self.gboard_width) / 2
        self.bottom_left_y = (cfg.window_height - self.gboard_height) / 2

        self.gcells = self.get_cell_coords()
        self.glines = self.get_lines_coords()
        self.exit_data = self.get_exit_data()
        self.triangle_texts: List[TriangleText] = []

        self.is_line_present = False
        self.is_solved = False

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

    def create_triangle_texts(self):
        self.triangle_texts = []
        for i, (row, grow) in enumerate(zip(self.board.triangle_values, self.gcells)):
            for j, (triangle_value, gcell) in enumerate(zip(row, grow)):
                x, y = gcell
                x += cfg.cell_size / 2
                y += cfg.cell_size / 2
                if triangle_value >= 1:
                    self.triangle_texts.append(TriangleText(triangle_value, i, j, x, y))

    def draw_board(self):
        arcade.draw_xywh_rectangle_filled(self.bottom_left_x, self.bottom_left_y,
                                          self.gboard_width, self.gboard_height,
                                          cfg.board_color[cfg.theme])
        for row in self.gcells:
            for x, y in row:
                arcade.draw_xywh_rectangle_filled(x, y, cfg.cell_size, cfg.cell_size, cfg.cell_color[cfg.theme])

    def draw_triangles(self):
        for triangle in self.triangle_texts:
            triangle.draw()

    def draw_start(self):
        if self.is_solved:
            color = cfg.solved_line_color
        elif self.is_line_present:
            color = cfg.line_color[cfg.theme]
        else:
            color = cfg.board_color[cfg.theme]

        self.draw_circle_at_position(self.board.start[1], self.board.start[0], color)

    def draw_exit(self):
        if self.exit_data:
            arcade.draw_xywh_rectangle_filled(self.exit_data.rect_x,
                                              self.exit_data.rect_y,
                                              self.exit_data.rect_w,
                                              self.exit_data.rect_h,
                                              cfg.board_color[cfg.theme])
            arcade.draw_circle_filled(self.exit_data.circle_x,
                                      self.exit_data.circle_y,
                                      self.exit_data.circle_radius,
                                      cfg.board_color[cfg.theme])
        else:
            # middle of the board
            color = cfg.solved_line_color if self.is_solved else cfg.board_color[cfg.theme]
            self.draw_rectangle_at_position(self.board.exit[1], self.board.exit[0], color)

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
        arcade.draw_line_strip([self.glines[x][y] for x, y in self.board.solution_line],
                               cfg.solution_color, line_width=cfg.player_line_width)

    def draw_line(self, line: List[Node]):
        if self.is_line_present:
            color = cfg.solved_line_color if self.is_solved else cfg.line_color[cfg.theme]
            arcade.draw_line_strip([self.glines[x][y] for x, y in line],
                                   color, line_width=cfg.player_line_width)

    def draw_hints(self, hints: List[Node]):
        arcade.draw_lines([self.glines[x][y] for x, y in hints],
                          cfg.hint_color, line_width=cfg.player_line_width)

    @staticmethod
    def draw_help_tip():
        arcade.draw_text(f'F1 - Help',
                         cfg.text_left_margin, cfg.window_height - cfg.help_tip_top_margin,
                         anchor_x='left', anchor_y='top',
                         font_size=cfg.help_tip_font_size, color=cfg.help_tip_color)

    def draw_board_difficulty(self):
        arcade.draw_text(f'Difficulty: {round(self.board.difficulty)}',
                         cfg.window_width - cfg.text_left_margin,
                         cfg.window_height - cfg.help_tip_top_margin,
                         anchor_x='right', anchor_y='top',
                         font_size=cfg.help_tip_font_size, color=arcade.color.GOLD)

    @staticmethod
    def show_help_screen():
        levels = [cfg.window_height - cfg.help_top_margin - i * cfg.help_step for i in range(30)]

        arcade.draw_lrtb_rectangle_filled(cfg.help_main_margin, cfg.window_width - cfg.help_main_margin,
                                          cfg.window_height - cfg.help_main_margin, cfg.help_main_margin,
                                          color=cfg.help_bg_color)
        arcade.draw_lrtb_rectangle_outline(cfg.help_main_margin, cfg.window_width - cfg.help_main_margin,
                                           cfg.window_height - cfg.help_main_margin, cfg.help_main_margin,
                                           color=cfg.help_border_color, border_width=cfg.help_border_width)
        arcade.draw_text('HELP', cfg.window_width // 2, levels[0], anchor_x='center',
                         font_size=cfg.help_title_font_size, color=cfg.help_font_color,
                         font_name=cfg.help_font, bold=True)
        for i, line in enumerate((
                f'{"Esc":<{cfg.help_pad}}quit',
                f'{"arrows/WASD":<{cfg.help_pad}}move line',
                f'{"Space":<{cfg.help_pad}}start new puzzle',
                f'{"R":<{cfg.help_pad}}reset line',
                f'{"E":<{cfg.help_pad}}get a hint',
                f'{"H":<{cfg.help_pad}}show solution',
                f'{"Enter":<{cfg.help_pad}}copy puzzle code',
                f'{"T":<{cfg.help_pad}}change theme',
                f'{"F1":<{cfg.help_pad}}help',
        )):
            arcade.draw_text(line, cfg.help_text_margin, levels[i + 2], font_name=cfg.help_font,
                             anchor_x='left', font_size=cfg.help_font_size, color=cfg.help_font_color, bold=True)

    def mark_wrong_triangles(self, line: List[Node]):
        for triangle in self.triangle_texts:
            if triangle.num != get_triangle_value(triangle.cell_x, triangle.cell_y, line):
                triangle.color = cfg.wrong_triangle_color

    def reset_triangle_color(self):
        for triangle in self.triangle_texts:
            triangle.color = cfg.triangle_color[cfg.theme]

    @staticmethod
    def draw_custom_puzzle_text():
        arcade.draw_text(f'CUSTOM PUZZLE MODE',
                         cfg.window_width - cfg.text_left_margin,
                         cfg.help_tip_top_margin,
                         anchor_x='right', anchor_y='baseline',
                         font_size=cfg.help_tip_font_size, color=cfg.help_tip_color)

    def update_triangle_colors(self):
        for triangle in self.triangle_texts:
            triangle.color = cfg.triangle_color[cfg.theme]
