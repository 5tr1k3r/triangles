from typing import Optional

import arcade

from views.menu_view import MenuView
from views.play_view import PlayView
from views.solve_view import SolveView


class ViewManager:
    def __init__(self):
        self.window: Optional[arcade.Window] = None
        self.menu = MenuView()
        self.solver = SolveView()

    def confirm_window_exists(self):
        if self.window is None:
            self.window = arcade.get_window()

    def show_menu_view(self):
        self.confirm_window_exists()
        self.window.show_view(self.menu)

    def show_play_view(self):
        self.confirm_window_exists()
        self.window.show_view(PlayView())

    def show_play_view_with_custom_puzzle(self, puzzle_code: str):
        self.confirm_window_exists()
        self.window.show_view(PlayView(puzzle_code))

    def show_solve_view(self):
        self.confirm_window_exists()
        self.window.show_view(self.solver)
