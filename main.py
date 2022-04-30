import arcade

import config as cfg
from game_drawing import HelpScreen, Popup
from views.view_manager import ViewManager


class Triangles(arcade.Window):
    def __init__(self):
        super().__init__(cfg.window_width, cfg.window_height, 'Triangles', center_window=True)

        self.help = HelpScreen()
        self.popup = Popup()
        self.vm = ViewManager()
        self.vm.show_menu_view()

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
