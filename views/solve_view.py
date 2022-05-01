import math
from typing import Tuple, List, Optional

import arcade
import arcade.gui
import pyperclip

import config as cfg
from game_drawing import GameDrawing
from models import Board, FullPath


class SolveView(arcade.View):
    def __init__(self, custom_puzzle_code: Optional[str] = None):
        super().__init__()

        self.board = Board(width=cfg.board_width,
                           height=cfg.board_height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)

        if custom_puzzle_code is not None:
            self.is_custom_puzzle = True
            self.board.load_custom_puzzle(custom_puzzle_code)

        self.gd: Optional[GameDrawing] = None
        self.refresh_gui()

        self.ui = arcade.gui.UIManager()
        self.ui.enable()

        self.bottom_ui_panel = arcade.gui.UIBoxLayout(vertical=False)
        self.top_ui_panel = arcade.gui.UIBoxLayout(vertical=False)
        self.add_ui_buttons()

        self.is_selecting_start = False
        self.is_selecting_exit = False
        self.solutions: List[FullPath] = []
        self.current_solution = 0
        self.mouse_x = 0
        self.mouse_y = 0

    def refresh_gui(self, create_gd=True):
        if create_gd:
            self.gd = GameDrawing(self.board, 110)

        self.reset_solutions()
        self.board.solution_line = []
        self.gd.create_triangles()
        self.board.estimate_difficulty()

    def add_ui_buttons(self):
        texts = ('Solve', 'Play', 'Move start', 'Move exit')
        funcs = (self.solve_puzzle, self.play_puzzle, self.move_start, self.move_exit)

        for text, func in zip(texts, funcs):
            button = arcade.gui.UIFlatButton(text=text, width=cfg.button_width, height=cfg.button_height)
            self.bottom_ui_panel.add(button)
            button.on_click = func

        self.ui.add(arcade.gui.UIAnchorWidget(anchor_x='center', anchor_y='bottom',
                                              align_y=cfg.bottom_panel_margin,
                                              child=self.bottom_ui_panel))

        # assets downloaded from https://kenney.nl/
        filenames = ('first.png', 'previous.png', 'next.png', 'last.png')
        funcs = (self.show_first_solution, self.show_previous_solution,
                 self.show_next_solution, self.show_last_solution)

        for filename, func in zip(filenames, funcs):
            texture = arcade.load_texture(f'assets/img/{filename}')
            button = arcade.gui.UITextureButton(texture=texture, scale=0.5)
            self.top_ui_panel.add(button)
            button.on_click = func

        self.ui.add(arcade.gui.UIAnchorWidget(anchor_x='center', anchor_y='bottom',
                                              align_y=cfg.top_panel_margin,
                                              child=self.top_ui_panel))

    def reset_solutions(self):
        self.solutions = []
        self.current_solution = 0

    def on_show_view(self):
        self.ui.enable()
        self.window.help.create_texts([
            ("Esc", 'quit to menu'),
            ('LMB', 'add triangles'),
            ('RMB', 'clear triangles'),
            ("Space", 'solve'),
            ("R", 'reset board'),
            ("arrows", 'change board size'),
            ("UIOP", 'navigate solutions'),
            ("Enter", 'copy puzzle code'),
        ])
        arcade.set_background_color(cfg.bg_color[cfg.theme])

    def on_hide_view(self):
        self.ui.disable()

    def on_draw(self):
        self.clear()

        self.gd.draw_board_without_start_and_exit()

        self.ui.draw()

        if self.is_selecting_start:
            self.gd.draw_start_cursor(self.mouse_x, self.mouse_y)
        else:
            self.gd.draw_start()

        if self.is_selecting_exit:
            self.gd.draw_exit_cursor(self.mouse_x, self.mouse_y)
        else:
            self.gd.draw_exit()

        if self.board.solution_line:
            self.gd.draw_solution()
        self.gd.draw_board_difficulty()

        if self.is_selecting_lane_point():
            self.gd.draw_selecting_lane_point()
        if self.solutions:
            self.gd.draw_solution_info(self.current_solution, len(self.solutions),
                                       len(self.solutions[self.current_solution]) - 1)

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
            self.refresh_gui(create_gd=False)
        elif symbol == arcade.key.U:
            self.show_first_solution()
        elif symbol == arcade.key.I:
            self.show_previous_solution()
        elif symbol == arcade.key.O:
            self.show_next_solution()
        elif symbol == arcade.key.P:
            self.show_last_solution()
        elif symbol in (arcade.key.LEFT, arcade.key.UP, arcade.key.RIGHT, arcade.key.DOWN):
            board_width = self.board.width
            board_height = self.board.height
            if symbol == arcade.key.LEFT:
                board_width -= 1
            elif symbol == arcade.key.UP:
                board_height += 1
            elif symbol == arcade.key.RIGHT:
                board_width += 1
            elif symbol == arcade.key.DOWN:
                board_height -= 1

            if 1 <= board_width <= cfg.max_board_width and 1 <= board_height <= cfg.max_board_width:
                self.resize_board(board_width, board_height)

    def is_selecting_lane_point(self) -> bool:
        return self.is_selecting_start or self.is_selecting_exit

    def stop_selecting_lane_point(self):
        self.is_selecting_start = False
        self.is_selecting_exit = False
        self.window.set_mouse_visible(True)

    def solve_puzzle(self, _event=None):
        if not self.solutions:
            solutions = self.board.solve()
            if solutions:
                self.solutions = solutions
                self.board.solution_line = solutions[0]
            else:
                self.window.popup.set('No solution found!')

    def play_puzzle(self, _event=None):
        solutions = self.board.solve()
        if not solutions:
            self.window.popup.set('Not solvable, cannot play this')
            return

        code = self.board.generate_code(solutions[0])
        self.window.vm.show_play_view_with_custom_puzzle(code)

    def move_start(self, _event=None):
        self.window.set_mouse_visible(False)
        self.window.popup.set('Selecting start...')
        self.is_selecting_start = True

    def move_exit(self, _event=None):
        self.window.set_mouse_visible(False)
        self.window.popup.set('Selecting exit...')
        self.is_selecting_exit = True

    # noinspection PyUnresolvedReferences
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.is_selecting_lane_point():
            lane_x, lane_y = self.select_lane_point(x, y)
            self.move_start_or_exit(lane_x, lane_y)
            self.stop_selecting_lane_point()
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
            self.refresh_gui(create_gd=False)

    def resize_board(self, width: int, height: int):
        self.board = Board(width=width,
                           height=height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)
        self.refresh_gui()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_x = x
        self.mouse_y = y

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
        self.refresh_gui()

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

    def show_solution_n(self, n: int):
        if not self.solutions or n < 0 or n > len(self.solutions) - 1:
            return

        self.current_solution = n
        self.board.solution_line = self.solutions[n]

    def show_first_solution(self, _event=None):
        self.show_solution_n(0)

    def show_previous_solution(self, _event=None):
        self.show_solution_n(self.current_solution - 1)

    def show_next_solution(self, _event=None):
        self.show_solution_n(self.current_solution + 1)

    def show_last_solution(self, _event=None):
        self.show_solution_n(len(self.solutions) - 1)
