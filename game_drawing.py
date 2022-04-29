import math
from dataclasses import dataclass
from typing import Tuple, List, Optional

import arcade
from PIL import Image, ImageDraw
from arcade.experimental.lights import Light, LightLayer

import config as cfg
from models import Board, Node, get_triangle_value

Coords = Tuple[float, float]


@dataclass
class TriangleCoords:
    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    middle_x: float
    middle_y: float

    def shift_horizontally(self, val: float):
        x1 = self.x1 + val
        x2 = self.x2 + val
        x3 = self.x3 + val
        middle_x = self.middle_x + val

        return TriangleCoords(x1, self.y1, x2, self.y2, x3, self.y3, middle_x, self.middle_y)


class Triangle:
    def __init__(self, num: int, x: int, y: int,
                 start_x: float, start_y: float):
        self.num = num
        self.cell_x = x
        self.cell_y = y
        self.color = cfg.triangle_color

        self.triangle_coords: List[TriangleCoords] = []
        self.find_triangle_coords(start_x, start_y)

        self.lights: List[Light] = []
        for t in self.triangle_coords:
            self.lights.append(Light(t.middle_x, t.middle_y,
                                     cfg.triangle_size * 1.15,
                                     cfg.triangle_lights_color[cfg.theme],
                                     'soft'))

    def find_triangle_coords(self, x: float, y: float):
        margin = 4
        bottom_offset = cfg.triangle_size * math.sqrt(3) / 6
        top_offset = cfg.triangle_size * math.sqrt(3) / 3
        double_triangle_offset = (cfg.triangle_size + margin) / 2

        # left
        x1 = x - cfg.triangle_size / 2
        y1 = y - bottom_offset
        # top
        x2 = x
        y2 = y + top_offset
        # right
        x3 = x1 + cfg.triangle_size
        y3 = y1

        coords_a = TriangleCoords(x1, y1, x2, y2, x3, y3, x, y)
        if self.num == 1:
            self.triangle_coords.append(coords_a)
            return

        coords_b = coords_a.shift_horizontally(cfg.triangle_size + margin)
        coords_c = coords_a.shift_horizontally(-(cfg.triangle_size + margin))

        if self.num == 3:
            self.triangle_coords += [coords_a, coords_b, coords_c]
            return

        coords_a = coords_a.shift_horizontally(-double_triangle_offset)
        coords_b = coords_b.shift_horizontally(-double_triangle_offset)
        self.triangle_coords += [coords_a, coords_b]


@dataclass
class GExitData:
    rect_x: float
    rect_y: float
    rect_w: float
    rect_h: float
    circle_x: float
    circle_y: float
    circle_radius: float


class Cell(arcade.Sprite):
    textures = []
    for cell_color in cfg.cell_color:
        cell_color = cell_color + (cfg.cell_alpha,)
        img = Image.new("RGBA", (cfg.cell_size, cfg.cell_size), cell_color)
        textures.append(arcade.Texture(name=str(cell_color), image=img, hit_box_algorithm=None))

    def __init__(self, left: float, bottom: float, x: int, y: int):
        super().__init__(texture=Cell.textures[cfg.theme])
        self.left = left
        self.bottom = bottom
        self.x = x
        self.y = y

    def reload_texture(self):
        self.texture = Cell.textures[cfg.theme]


class GBoard(arcade.Sprite):
    def __init__(self, width: int, height: int, left: float, bottom: float):
        self.gboard_textures = []
        for cell_color in cfg.board_color:
            texture = arcade.Texture.create_empty(f'gboard {cell_color}', (width, height))
            draw = ImageDraw.Draw(texture.image)
            draw.rounded_rectangle([0, 0, width - 1, height - 1], cfg.lane_width // 2, cell_color)
            self.gboard_textures.append(texture)

        super().__init__(texture=self.gboard_textures[cfg.theme])
        self.left = left
        self.bottom = bottom

    def reload_texture(self):
        self.texture = self.gboard_textures[cfg.theme]


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
        self.triangles: List[Triangle] = []

        self.cells = arcade.SpriteList()
        self.create_cell_sprites()
        self.gboard = GBoard(self.gboard_width, self.gboard_height, self.bottom_left_x, self.bottom_left_y)
        self.gboard_list = arcade.SpriteList()
        self.gboard_list.append(self.gboard)

        self.is_line_present = False
        self.is_solved = False

        self.light_layer = LightLayer(cfg.window_width, cfg.window_height)
        self.light_layer.set_background_color(cfg.bg_color[cfg.theme])

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
                rect_y = self.bottom_left_y + self.gboard_height - dim_b
                circle_y = rect_y + dim_a + dim_b
            else:
                rect_y = self.bottom_left_y - dim_a
                circle_y = rect_y

            return GExitData(rect_x=rect_x + offset_x, rect_y=rect_y,
                             rect_w=cfg.lane_width, rect_h=dim_a + dim_b,
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

    def create_triangles(self):
        self.triangles = []
        self.light_layer._lights = []
        for i, (row, grow) in enumerate(zip(self.board.triangle_values, self.gcells)):
            for j, (triangle_value, gcell) in enumerate(zip(row, grow)):
                x, y = gcell
                x += cfg.cell_size / 2
                y += cfg.cell_size / 2
                if triangle_value >= 1:
                    triangle = Triangle(triangle_value, i, j, x, y)
                    self.triangles.append(triangle)
                    self.light_layer.extend(triangle.lights)

    def draw_board(self):
        with self.light_layer:
            self.gboard_list.draw()
            self.cells.draw()

        self.draw_light_layer()
        self.draw_triangles()
        self.draw_start()
        self.draw_exit()

    def draw_light_layer(self):
        self.light_layer.draw(ambient_color=arcade.color.WHITE)

    def draw_triangles(self):
        for triangle in self.triangles:
            for t in triangle.triangle_coords:
                arcade.draw_triangle_filled(t.x1, t.y1, t.x2, t.y2, t.x3, t.y3, triangle.color)

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

    def draw_board_difficulty(self):
        arcade.draw_text(f'Difficulty: {round(self.board.difficulty)}',
                         cfg.window_width - cfg.text_left_margin,
                         cfg.window_height - cfg.help_tip_top_margin,
                         anchor_x='right', anchor_y='top',
                         font_size=cfg.help_tip_font_size, color=arcade.color.GOLD)

    def mark_wrong_triangles(self, line: List[Node]):
        for triangle in self.triangles:
            if triangle.num != get_triangle_value(triangle.cell_x, triangle.cell_y, line):
                triangle.color = cfg.wrong_triangle_color
                for light in triangle.lights:
                    light._color = cfg.wrong_triangle_color
                self.light_layer._rebuild = True

    def reset_triangle_color(self):
        self.update_triangle_lights_colors()
        for triangle in self.triangles:
            triangle.color = cfg.triangle_color

    @staticmethod
    def draw_custom_puzzle_text():
        arcade.draw_text(f'CUSTOM PUZZLE MODE',
                         cfg.window_width - cfg.text_left_margin,
                         cfg.help_tip_top_margin,
                         anchor_x='right', anchor_y='baseline',
                         font_size=cfg.help_tip_font_size, color=cfg.help_tip_color)

    def update_triangle_lights_colors(self):
        for light in self.light_layer._lights:
            light._color = cfg.triangle_lights_color[cfg.theme]
        self.light_layer._rebuild = True

    def create_cell_sprites(self):
        for i, row in enumerate(self.gcells):
            for j, (x, y) in enumerate(row):
                cell = Cell(x, y, i, j)
                self.cells.append(cell)

    def reload_cell_textures(self):
        for cell in self.cells:
            cell: Cell
            cell.reload_texture()


class MenuOption:
    def __init__(self, text: str, x: float, y: float):
        self.text = arcade.Text(text, x, y,
                                cfg.menu_font_color, cfg.menu_font_size,
                                anchor_x='center', anchor_y='center')
        self.is_hovered = False

    def refresh_hover_status(self, mouse_x: float, mouse_y: float):
        new_hover_status = self.is_hovered_over(mouse_x, mouse_y)
        if new_hover_status != self.is_hovered:
            self.is_hovered = new_hover_status
            self.text.color = cfg.menu_active_color if new_hover_status else cfg.menu_font_color

    def is_hovered_over(self, mouse_x: float, mouse_y: float) -> bool:
        half_width = self.text.content_width / 2
        half_height = self.text.content_height / 2
        a = self.text.x - half_width
        b = self.text.x + half_width
        c = self.text.y - half_height
        d = self.text.y + half_height
        return a <= mouse_x <= b and c <= mouse_y <= d


class HelpScreen:
    def __init__(self):
        self.is_shown = False

        self.tip = arcade.Text(f'F1 - Help',
                               cfg.text_left_margin, cfg.window_height - cfg.help_tip_top_margin,
                               anchor_x='left', anchor_y='top',
                               font_size=cfg.help_tip_font_size, color=cfg.help_tip_color)

        self.texts = []

    def create_texts(self, lines: List[Tuple[str, str]]):
        levels = [cfg.window_height - cfg.help_top_margin - i * cfg.help_step for i in range(30)]
        self.texts = [arcade.Text('HELP', cfg.window_width // 2, levels[0], anchor_x='center',
                                  font_size=cfg.help_title_font_size, color=cfg.help_font_color,
                                  font_name=cfg.help_font, bold=True)]

        for i, (key, desc) in enumerate(lines):
            self.texts.append(arcade.Text(f'{key:<{cfg.help_pad}}{desc}', cfg.help_text_margin,
                                          levels[i + 2], font_name=cfg.help_font,
                                          anchor_x='left', font_size=cfg.help_font_size,
                                          color=cfg.help_font_color, bold=True))

    def show(self):
        if not self.is_shown or not self.texts:
            return

        arcade.draw_lrtb_rectangle_filled(cfg.help_main_margin, cfg.window_width - cfg.help_main_margin,
                                          cfg.window_height - cfg.help_main_margin, cfg.help_main_margin,
                                          color=cfg.help_bg_color)
        arcade.draw_lrtb_rectangle_outline(cfg.help_main_margin, cfg.window_width - cfg.help_main_margin,
                                           cfg.window_height - cfg.help_main_margin, cfg.help_main_margin,
                                           color=cfg.help_border_color, border_width=cfg.help_border_width)

        for text in self.texts:
            text.draw()

    def draw_tip(self):
        if not self.texts:
            return

        self.tip.draw()


class Popup:
    def __init__(self):
        self.alpha = 255
        self.text = None

    def set(self, text: str, color=cfg.popup_color[cfg.theme]):
        print(text)
        self.alpha = 255
        self.text = arcade.Text(text, cfg.window_width / 2, cfg.window_height - cfg.popup_top_margin,
                                anchor_x='center', anchor_y='center',
                                font_size=cfg.popup_font_size,
                                color=color)

    def show(self):
        if self.text:
            self.text.color = self.text.color[:3] + (self.alpha,)
            self.text.draw()

    def update(self):
        if self.text:
            new_alpha = max(0, self.alpha - cfg.popup_alpha_step)
            self.alpha = new_alpha
            if new_alpha == 0:
                self.text = None
