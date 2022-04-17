import arcade
import toml

try:
    with open('custom_config.toml') as f:
        cc = toml.load(f)
except FileNotFoundError:
    cc = {}

window_width = cc.get('window_width', 1000)
window_height = cc.get('window_height', 1000)

cell_size = cc.get('cell_size', 70)
line_width = cc.get('line_width', 20)
start_radius = cc.get('start_radius', 24)

bg_color = arcade.color.SMOKY_BLACK
board_color = (130, 110, 45)
cell_color = arcade.color.SMOKY_BLACK
solution_color = arcade.color.RED
triangle_color = arcade.color.YELLOW
line_color = (254, 213, 135)
solved_line_color = (254, 158, 1)

hide_triangle_probability = cc.get('hide_triangle_probability', 0.4)
