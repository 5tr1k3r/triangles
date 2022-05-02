import random
import time
from typing import List, Set, Optional
import numpy as np

import arcade
import arcade.gui
import pyperclip

import config as cfg
from game_drawing import GameDrawing
from models import Board, Node, PuzzleStats


class PlayView(arcade.View):
    def __init__(self, custom_puzzle_code: Optional[str] = None):
        super().__init__()

        self.board = Board(width=cfg.board_width,
                           height=cfg.board_height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)

        if custom_puzzle_code is not None:
            self.is_custom_puzzle = True
            self.board.load_custom_puzzle(custom_puzzle_code)
        else:
            self.is_custom_puzzle = False
            self.board.generate_paths()

        self.gd = GameDrawing(self.board)

        self.ui = arcade.gui.UIManager()
        self.ui.enable()

        self.solve_button = arcade.gui.UIFlatButton(text='Open in solver', width=200)
        self.solve_button.on_click = self.open_in_solver

        self.ui.add(arcade.gui.UIAnchorWidget(anchor_x='center', anchor_y='bottom',
                                              align_y=cfg.bottom_panel_margin,
                                              child=self.solve_button))

        self.is_show_solution = False
        self.line: List[Node] = [self.board.start]
        self.hints: List[Node] = []
        self.hints_used: Set[int] = set()
        self.is_solved = False
        self.is_validated_line = False
        self.has_been_solved_already = False
        self.puzzle_start_time = None
        self.puzzle_index = 0
        self.was_solution_shown = False
        self.was_given_space_warning = False
        self.puzzle_stats: List[PuzzleStats] = []

        self.mouse_x = cfg.window_width / 2
        self.mouse_y = cfg.window_height / 2
        self.mouse_anchor_x = 0
        self.mouse_anchor_y = 0
        self.is_mouse_mode = False
        self.is_keyboard_mode = False
        self.mouse_directions = None

        self.start_new_puzzle()

    def on_show_view(self):
        self.window.set_mouse_visible(False)
        self.ui.enable()
        self.window.help.create_texts([
            ("Esc", 'quit to menu'),
            ("arrows/WASD", 'move line'),
            ("Space", 'start new puzzle'),
            ("R", 'reset line'),
            ("E", 'get a hint'),
            ("H", 'show solution'),
            ("Enter", 'copy puzzle code'),
            ("T", 'change theme'),
            ("Z", 'undo'),
        ])
        arcade.set_background_color(cfg.bg_color[cfg.theme])

    def on_hide_view(self):
        self.window.set_mouse_visible(True)
        self.ui.disable()

    def start_new_puzzle(self):
        if not self.is_custom_puzzle:
            self.board.get_solution_line()
            self.board.find_triangle_values()
        self.board.estimate_difficulty()
        self.gd.create_triangles()

        self.is_show_solution = False
        self.line = [self.board.start]
        self.hints = []
        self.hints_used = set()
        self.is_solved = False
        self.is_validated_line = False
        self.has_been_solved_already = False

        self.puzzle_start_time = time.time()
        self.puzzle_index += 1
        self.was_solution_shown = False
        self.was_given_space_warning = False
        self.is_mouse_mode = False
        self.is_keyboard_mode = False
        self.mouse_anchor_x = 0
        self.mouse_anchor_y = 0

    def on_draw(self):
        self.clear()

        self.gd.draw_board()
        self.gd.draw_line(self.line)
        if self.is_need_to_show_hints():
            self.gd.draw_hints(self.hints)
        if self.is_show_solution:
            self.gd.draw_solution()
        self.gd.draw_board_difficulty()
        self.ui.draw()
        if self.is_custom_puzzle:
            self.gd.draw_custom_puzzle_text()

        if self.is_mouse_mode:
            x, y = self.normalize_mouse_coords(self.mouse_x, self.mouse_y)
            self.gd.draw_mouse_line_segment(self.mouse_anchor_x, self.mouse_anchor_y, x, y)
        self.gd.draw_mouse_cursor(self.mouse_x, self.mouse_y)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        if self.is_mouse_mode:
            max_step = 100

            # 1 0 up
            # 0 1 right
            # -1 0 down
            # 0 -1 left
            if self.mouse_directions is None:
                self.mouse_directions = self.get_available_directions()

            x_array = self.mouse_directions[:, 0]
            y_array = self.mouse_directions[:, 1]
            min_x = x_array.min()
            max_x = x_array.max()
            min_y = y_array.min()
            max_y = y_array.max()

            start_x, start_y = self.gd.glines[self.mouse_anchor_x][self.mouse_anchor_y]

            if start_x + max_step * min_x <= x <= start_x + max_step * max_x:
                self.mouse_x += dx
            if start_y + max_step * min_y <= y <= start_y + max_step * max_y:
                self.mouse_y += dy

        else:
            self.mouse_x = x
            self.mouse_y = y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # right click
        if button == 4:
            self.stop_mouse_mode()
            return

        if not self.is_keyboard_mode and self.is_click_inside_start_zone(x, y):
            self.start_mouse_mode()

            self.mouse_anchor_x, self.mouse_anchor_y = self.board.start

    @staticmethod
    def normalize_mouse_coords(x: float, y: float):
        # todo
        return x, y

    def is_line_present(self) -> bool:
        return len(self.line) > 1

    def start_mouse_mode(self):
        if not self.is_mouse_mode:
            print('starting mouse mode')
        self.is_mouse_mode = True

    def stop_mouse_mode(self):
        if self.is_mouse_mode:
            print('stopping mouse mode')
        self.is_mouse_mode = False

    def start_keyboard_mode(self):
        if not self.is_keyboard_mode:
            print('starting keyboard mode')
        self.is_keyboard_mode = True

    def stop_keyboard_mode(self):
        if self.is_keyboard_mode:
            print('stopping keyboard mode')
        self.is_keyboard_mode = False

    def is_need_to_show_hints(self) -> bool:
        return self.hints and not self.is_show_solution and not self.is_solved

    def on_update(self, delta_time: float):
        self.gd.is_line_present = self.is_line_present()
        self.gd.is_solved = self.is_solved

        self.check_validation()

    def check_validation(self):
        if self.line[-1] == self.board.exit:
            if not self.is_validated_line:
                self.is_solved = self.board.check_solution(self.line)
                self.is_validated_line = True

                if not self.is_solved:
                    self.gd.mark_wrong_triangles(self.line)

                if self.is_solved and not self.has_been_solved_already:
                    self.show_resulting_time()
                    self.has_been_solved_already = True
        elif self.is_validated_line:
            self.is_validated_line = False
            self.is_solved = False
            self.gd.reset_triangle_color()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.display_final_stats()
            self.window.vm.show_menu_view()
        elif symbol == arcade.key.H:
            self.was_solution_shown = True
            self.is_show_solution = not self.is_show_solution
        elif symbol == arcade.key.R:
            self.line = [self.board.start]
            self.stop_keyboard_mode()
        elif symbol in (arcade.key.LEFT, arcade.key.UP, arcade.key.RIGHT, arcade.key.DOWN,
                        arcade.key.A, arcade.key.W, arcade.key.D, arcade.key.S):
            if self.is_mouse_mode:
                return

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

            if self.is_line_present():
                self.start_keyboard_mode()
            else:
                self.stop_keyboard_mode()

        elif symbol == arcade.key.SPACE:
            if self.is_custom_puzzle:
                self.window.popup.set('Not available in custom puzzle mode')
                return

            if self.has_been_solved_already or self.was_given_space_warning:
                self.start_new_puzzle()
            else:
                self.window.popup.set('Press Space again to confirm...')
                self.was_given_space_warning = True
        elif symbol == arcade.key.E:
            self.get_hint()
        elif symbol == arcade.key.ENTER:
            code = self.board.generate_code()
            pyperclip.copy(code)
            self.window.popup.set('Puzzle code copied')
        elif symbol == arcade.key.T:
            cfg.theme = int(not cfg.theme)
            arcade.set_background_color(cfg.bg_color[cfg.theme])
            self.gd.light_layer.set_background_color(cfg.bg_color[cfg.theme])
            self.gd.update_triangle_lights_colors()
            self.gd.reload_cell_textures()
            self.gd.gboard.reload_texture()
        elif symbol == arcade.key.Z:
            self.undo()

    def is_reverting(self, move: Node) -> bool:
        return self.is_line_present() and move == self.line[-2]

    def undo(self):
        if self.is_line_present():
            self.line = self.line[:-1]

    def is_valid_move(self, move: Node) -> bool:
        x, y = move
        if not (0 <= x <= self.board.height and 0 <= y <= self.board.width):
            return False

        if move in self.line:
            return False

        return True

    def show_resulting_time(self):
        result_time = time.time() - self.puzzle_start_time
        self.puzzle_stats.append(PuzzleStats(result_time, self.board.difficulty))
        text = f'Puzzle {self.puzzle_index} solved! Took {result_time:.1f}s'
        if self.was_solution_shown:
            text += ' and solution reveal'
        elif self.hints_used:
            num = len(self.hints_used)
            s = 's' if num > 1 else ''
            text += f' and {num} hint{s}'
        self.window.popup.set(text)

    def get_hint(self):
        all_solution_segments = set(range(len(self.board.solution_line) - 1))
        valid_hint_choices = list(all_solution_segments - self.hints_used)
        if not valid_hint_choices:
            self.window.popup.set('Ran out of hints :D')
            return

        chosen_hint = random.choice(valid_hint_choices)
        self.hints_used.add(chosen_hint)
        self.hints += self.board.solution_line[chosen_hint:chosen_hint + 2]

    def display_final_stats(self):
        puzzles_solved = len(self.puzzle_stats)
        if puzzles_solved:
            print(f'Solved {puzzles_solved} {self.board.width}x{self.board.height} puzzles total, '
                  f'avg time spent '
                  f'{(sum(x.time_spent for x in self.puzzle_stats) / puzzles_solved):.1f}s, '
                  f'avg puzzle difficulty '
                  f'{(sum(x.difficulty for x in self.puzzle_stats) / puzzles_solved):.1f}')

    def open_in_solver(self, _event=None):
        code = self.board.generate_code()
        self.window.vm.show_solve_view_with_custom_puzzle(code)

    def is_click_inside_start_zone(self, x: float, y: float):
        i, j = self.board.start
        start_x, start_y = self.gd.glines[i][j]
        half_width = cfg.start_radius * 1.1
        return (start_x - half_width <= x <= start_x + half_width and
                start_y - half_width <= y <= start_y + half_width)

    def get_available_directions(self):
        x, y = self.mouse_anchor_x, self.mouse_anchor_y
        all_directions = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]

        return np.array([(np.sign(x), np.sign(y)) for x, y in all_directions if 0 <= x <= self.board.width and
                         0 <= y <= self.board.height and (x, y) not in self.line])
