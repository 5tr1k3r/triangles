import arcade
import toml

try:
    with open('custom_config.toml') as f:
        cc = toml.load(f)
except FileNotFoundError:
    cc = {}

window_width = cc.get('window_width', 800)
window_height = cc.get('window_height', 800)

cell_size = cc.get('cell_size', 70)
lane_width = cc.get('line_width', 20)
start_radius = cc.get('start_radius', 24)
player_line_width = cc.get('player_line_width', 10)
triangle_text_size = cc.get('triangle_text_size', 16)

bg_color = arcade.color.SMOKY_BLACK
board_color = (130, 110, 45)
cell_color = arcade.color.SMOKY_BLACK
solution_color = arcade.color.RED + (170,)
triangle_color = arcade.color.YELLOW
line_color = (254, 213, 135)
solved_line_color = (254, 158, 1)

board_width = cc.get('board_width', 4)
board_height = cc.get('board_height', 4)
board_start = cc.get('board_start', [0, 0])
board_exit = cc.get('board_exit', None)     # by default the exit is at the top right corner

hide_triangle_probability = cc.get('hide_triangle_probability', 0.4)
max_paths_generated = cc.get('max_paths_generated', 10000)
generation_time_limit = cc.get('generation_time_limit', 1.0)
