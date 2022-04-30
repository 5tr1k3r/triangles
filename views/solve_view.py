import math
from typing import Tuple

import arcade
import pyperclip

import config as cfg
from game_drawing import GameDrawing, Button
from models import Board


class SolveView(arcade.View):
    def __init__(self):
        super().__init__()

        self.board = Board(width=cfg.board_width,
                           height=cfg.board_height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)

        self.gd = None
        self.create_game_drawing()

        self.window.help.create_texts([
            ("Esc", 'quit to menu'),
            ('LMB', 'add triangles'),
            ('RMB', 'clear triangles'),
            ("Space", 'solve'),
            ("R", 'reset board'),
            ("arrows/WASD", 'change board size'),
            ("Enter", 'copy puzzle code'),
        ])

        self.solve_button = Button('SOLVE', cfg.window_width / 2, cfg.solve_button_bottom_margin)
        self.solve_button_list = arcade.SpriteList()
        self.solve_button_list.append(self.solve_button)

        self.move_start_btn = Button('Move start', cfg.window_width * 0.2, cfg.solve_button_bottom_margin)
        self.move_start_list = arcade.SpriteList()
        self.move_start_list.append(self.move_start_btn)

        self.move_exit_btn = Button('Move exit', cfg.window_width * 0.8, cfg.solve_button_bottom_margin)
        self.move_exit_list = arcade.SpriteList()
        self.move_exit_list.append(self.move_exit_btn)

        self.play_btn = Button('Play', cfg.window_width * 0.5, cfg.solve_button_bottom_margin * 4)
        self.play_btn_list = arcade.SpriteList()
        self.play_btn_list.append(self.play_btn)

        self.is_selecting_start = False
        self.is_selecting_exit = False

    def create_game_drawing(self):
        self.gd = GameDrawing(self.board, 90 + cfg.solve_button_bottom_margin * 2)

    def on_show(self):
        arcade.set_background_color(cfg.bg_color[cfg.theme])

    def on_draw(self):
        self.clear()

        self.gd.draw_board()
        if self.board.solution_line:
            self.gd.draw_solution()
        self.gd.draw_board_difficulty()
        self.solve_button.draw()
        self.move_start_btn.draw()
        self.move_exit_btn.draw()
        self.play_btn.draw()
        if self.is_selecting_lane_point():
            self.gd.draw_selecting_lane_point()

    def on_key_press(self, symbol: int, modifiers: int):
        if self.is_selecting_lane_point() and symbol == arcade.key.ESCAPE:
            self.stop_selecting_lane_point()
            return

        if symbol == arcade.key.ESCAPE:
            self.window.vm.show_menu_view()
        elif symbol == arcade.key.SPACE:
            self.solve_puzzle()
        elif symbol == arcade.key.ENTER:
            solutions = self.board.solve()
            if not solutions:
                self.window.popup.set('No solution, cannot copy code')
                return

            code = self.board.generate_code(solutions[0])
            pyperclip.copy(code)
            self.window.popup.set('Puzzle code copied')
        elif symbol == arcade.key.R:
            self.board.reset()
            self.gd.create_triangles()
        elif symbol in (arcade.key.LEFT, arcade.key.UP, arcade.key.RIGHT, arcade.key.DOWN,
                        arcade.key.A, arcade.key.W, arcade.key.D, arcade.key.S):
            board_width = self.board.width
            board_height = self.board.height
            if symbol in (arcade.key.LEFT, arcade.key.A):
                board_width -= 1
            elif symbol in (arcade.key.UP, arcade.key.W):
                board_height += 1
            elif symbol in (arcade.key.RIGHT, arcade.key.D):
                board_width += 1
            elif symbol in (arcade.key.DOWN, arcade.key.S):
                board_height -= 1

            if 1 <= board_width <= cfg.max_board_width and 1 <= board_height <= cfg.max_board_width:
                self.resize_board(board_width, board_height)

    def is_selecting_lane_point(self) -> bool:
        return self.is_selecting_start or self.is_selecting_exit

    def stop_selecting_lane_point(self):
        self.is_selecting_start = False
        self.is_selecting_exit = False

    def solve_puzzle(self):
        if not self.board.solution_line:
            solutions = self.board.solve()
            if solutions:
                self.board.solution_line = solutions[0]
            else:
                self.window.popup.set('No solution found!')

    # noinspection PyUnresolvedReferences
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.is_selecting_lane_point():
            lane_x, lane_y = self.select_lane_point(x, y)
            self.move_start_or_exit(lane_x, lane_y)
            self.stop_selecting_lane_point()
            return

        solve_button_list = arcade.get_sprites_at_point((x, y), self.solve_button_list)
        if solve_button_list:
            self.solve_puzzle()
            return

        move_start_list = arcade.get_sprites_at_point((x, y), self.move_start_list)
        if move_start_list:
            self.window.popup.set('Selecting start...')
            self.is_selecting_start = True
            return

        move_exit_list = arcade.get_sprites_at_point((x, y), self.move_exit_list)
        if move_exit_list:
            self.window.popup.set('Selecting exit...')
            self.is_selecting_exit = True
            return

        play_list = arcade.get_sprites_at_point((x, y), self.play_btn_list)
        if play_list:
            solutions = self.board.solve()
            if not solutions:
                self.window.popup.set('Not solvable, cannot play this')
                return

            code = self.board.generate_code(solutions[0])
            self.window.vm.show_play_view_with_custom_puzzle(code)
            return

        cells = arcade.get_sprites_at_point((x, y), self.gd.cells)
        if not cells:
            return

        cell = cells[0]
        change_detected = False

        # left click
        if button == 1:
            if self.board.triangle_values[cell.x][cell.y] < 3:
                self.board.triangle_values[cell.x][cell.y] += 1
                change_detected = True

        # right click
        elif self.board.triangle_values[cell.x][cell.y] > 0:
            self.board.triangle_values[cell.x][cell.y] = 0
            change_detected = True

        if change_detected:
            self.board.solution_line = []
            self.gd.create_triangles()
            self.board.estimate_difficulty()

    def resize_board(self, width: int, height: int):
        self.board = Board(width=width,
                           height=height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)
        self.create_game_drawing()

    def move_start_or_exit(self, x: int, y: int):
        bstart = self.board.start
        bexit = self.board.exit

        if self.is_selecting_start:
            if (x, y) == bexit:
                self.window.popup.set('Cannot move start to exit point!')
                return

            bstart = x, y
            self.window.popup.set(f'Start is now at {(x, y)}')

        elif self.is_selecting_exit:
            if (x, y) == bstart:
                self.window.popup.set('Cannot move exit to start point!')
                return

            bexit = x, y
            self.window.popup.set(f'Exit is now at {(x, y)}')

        triangles = self.board.triangle_values
        self.board = Board(width=self.board.width,
                           height=self.board.height,
                           bstart=bstart,
                           bexit=bexit)
        self.board.triangle_values = triangles
        self.board.estimate_difficulty()
        self.create_game_drawing()
        self.gd.create_triangles()

    def select_lane_point(self, mouse_x: float, mouse_y: float) -> Tuple[int, int]:
        low_dist = float('inf')
        low_x = 0
        low_y = 0

        for i, row in enumerate(self.gd.glines):
            for j, (x, y) in enumerate(row):
                dist = math.hypot(mouse_x - x, mouse_y - y)
                if dist < low_dist:
                    low_dist = dist
                    low_x = i
                    low_y = j

        return low_x, low_y
