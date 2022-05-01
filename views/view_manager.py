from typing import Optional, Dict

import arcade

from views.menu_view import MenuView
from views.play_view import PlayView
from views.solve_view import SolveView


class ViewManager:
    def __init__(self):
        self.window: Optional[arcade.Window] = None
        self.cached_views: Dict[str, arcade.View] = {}

    def confirm_window_exists(self):
        if self.window is None:
            self.window = arcade.get_window()

    def get_view_from_cache(self, view_type: type) -> arcade.View:
        name = view_type.__name__
        if name not in self.cached_views:
            self.cached_views[name] = view_type()

        return self.cached_views[name]

    def show_menu_view(self):
        self.confirm_window_exists()
        menu_view = self.get_view_from_cache(MenuView)
        self.window.show_view(menu_view)

    def show_play_view(self):
        self.confirm_window_exists()
        play_view = self.get_view_from_cache(PlayView)
        self.window.show_view(play_view)

    def show_play_view_with_custom_puzzle(self, puzzle_code: str):
        self.confirm_window_exists()

        # Not caching this because making it cacheable
        # would require a rework of the cache system,
        # e.g. key would need to contain the puzzle code/args.
        # Don't need to cache it that much anyway
        # because paths aren't generated and it works quickly regardless.
        self.window.show_view(PlayView(puzzle_code))

    def show_solve_view_with_custom_puzzle(self, puzzle_code: str):
        self.confirm_window_exists()
        self.window.show_view(SolveView(puzzle_code))

    def show_solve_view(self):
        self.confirm_window_exists()
        solve_view = self.get_view_from_cache(SolveView)
        self.window.show_view(solve_view)
