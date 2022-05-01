import random
import time
from typing import List, Set, Optional

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

        self.start_new_puzzle()

    def on_show_view(self):
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

    def is_line_present(self) -> bool:
        return len(self.line) > 1

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
        return len(self.line) >= 2 and move == self.line[-2]

    def undo(self):
        if len(self.line) >= 2:
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
