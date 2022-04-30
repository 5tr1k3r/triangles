import arcade

import config as cfg
from game_drawing import MenuOption


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        self.play = MenuOption('Play', cfg.window_width / 2, cfg.window_height / 2 + cfg.menu_vertical_margin * 2)
        self.play_custom = MenuOption('Play custom puzzle', cfg.window_width / 2,
                                      cfg.window_height / 2 + cfg.menu_vertical_margin)
        self.solve = MenuOption('Solve', cfg.window_width / 2, cfg.window_height / 2)
        self.quit = MenuOption('Quit', cfg.window_width / 2, cfg.window_height / 2 - cfg.menu_vertical_margin)
        self.options = [self.play, self.play_custom, self.solve, self.quit]

    def on_show_view(self):
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
            self.window.vm.show_play_view()

        elif self.play_custom.is_hovered:
            if cfg.custom_puzzle_code is None:
                self.window.popup.set('No puzzle code found', color=cfg.menu_popup_color)
                return

            self.window.vm.show_play_view_with_custom_puzzle(cfg.custom_puzzle_code)

        elif self.solve.is_hovered:
            self.window.vm.show_solve_view()

        elif self.quit.is_hovered:
            arcade.close_window()
