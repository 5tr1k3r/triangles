import math
import random
import time
from typing import List, Set, Tuple

import arcade
import pyperclip

import config as cfg
from game_drawing import GameDrawing, MenuOption, HelpScreen, Popup, Button
from models import Board, Node, PuzzleStats


class PlayView(arcade.View):
    def __init__(self, is_custom_puzzle: bool = False):
        super().__init__()

        self.board = Board(width=cfg.board_width,
                           height=cfg.board_height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)

        if is_custom_puzzle:
            self.is_custom_puzzle = True
            self.board.load_custom_puzzle(cfg.custom_puzzle_code)
        else:
            self.is_custom_puzzle = False
            self.board.generate_paths()

        self.gd = GameDrawing(self.board)
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

        arcade.set_background_color(cfg.bg_color[cfg.theme])

        self.start_new_puzzle()

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
            self.window.show_view(MenuView())
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


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        self.play = MenuOption('Play', cfg.window_width / 2, cfg.window_height / 2 + cfg.menu_vertical_margin * 2)
        self.play_custom = MenuOption('Play custom puzzle', cfg.window_width / 2,
                                      cfg.window_height / 2 + cfg.menu_vertical_margin)
        self.solve = MenuOption('Solve', cfg.window_width / 2, cfg.window_height / 2)
        self.quit = MenuOption('Quit', cfg.window_width / 2, cfg.window_height / 2 - cfg.menu_vertical_margin)
        self.options = [self.play, self.play_custom, self.solve, self.quit]

    def on_show(self):
        self.window.help.texts = []
        arcade.set_background_color(cfg.menu_bg_color)

    def on_draw(self):
        self.clear()
        for option in self.options:
            option.text.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        for option in self.options:
            option.refresh_hover_status(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.play.is_hovered:
            self.window.show_view(PlayView())

        elif self.play_custom.is_hovered:
            if cfg.custom_puzzle_code is None:
                self.window.popup.set('No puzzle code found', color=cfg.menu_popup_color)
                return

            self.window.show_view(PlayView(is_custom_puzzle=True))

        elif self.solve.is_hovered:
            self.window.show_view(SolveView())

        elif self.quit.is_hovered:
            arcade.close_window()


class SolveView(arcade.View):
    def __init__(self):
        super().__init__()

        self.board = Board(width=cfg.board_width,
                           height=cfg.board_height,
                           bstart=cfg.board_start,
                           bexit=cfg.board_exit)

        self.gd = GameDrawing(self.board)
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

        self.is_selecting_start = False
        self.is_selecting_exit = False

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
        if self.is_selecting_lane_point():
            self.gd.draw_selecting_lane_point()

    def on_key_press(self, symbol: int, modifiers: int):
        if self.is_selecting_lane_point() and symbol == arcade.key.ESCAPE:
            self.stop_selecting_lane_point()
            return

        if symbol == arcade.key.ESCAPE:
            self.window.show_view(MenuView())
        elif symbol == arcade.key.SPACE:
            self.solve_puzzle()
        elif symbol == arcade.key.ENTER:
            solution = self.board.solve()
            if not solution:
                self.window.popup.set('No solution, cannot copy code')
                return

            code = self.board.generate_code(solution)
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
            solution = self.board.solve()
            if solution:
                self.board.solution_line = solution
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
        self.gd = GameDrawing(self.board)

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
        self.gd = GameDrawing(self.board)
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


class Triangles(arcade.Window):
    def __init__(self):
        super().__init__(cfg.window_width, cfg.window_height, 'Triangles', center_window=True)

        self.help = HelpScreen()
        self.popup = Popup()

        self.show_view(MenuView())

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.F1:
            self.help.is_shown = True

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == arcade.key.F1:
            self.help.is_shown = False

    def on_draw(self):
        self.help.draw_tip()
        self.popup.show()
        self.help.show()

    def on_update(self, delta_time: float):
        self.popup.update()


def main():
    Triangles()
    arcade.run()


if __name__ == '__main__':
    main()
