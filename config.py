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
lane_width = cc.get('lane_width', 20)
triangle_size = cc.get('triangle_size', 18)
start_radius = cc.get('start_radius', 24)
player_line_width = cc.get('player_line_width', 10)

# margin
text_left_margin = cc.get('text_left_margin', 20)

# help tip
help_tip_top_margin = cc.get('help_tip_top_margin', 20)
help_tip_font_size = cc.get('help_tip_font_size', 16)
help_tip_color = arcade.color.RED

help_main_margin = cc.get('help_main_margin', 50)
help_top_margin = cc.get('help_top_margin', 120)
help_text_margin = cc.get('help_text_margin', 150)
help_step = cc.get('help_step', 50)
help_pad = cc.get('help_pad', 14)
help_font = cc.get('help_font', "Courier New")
help_title_font_size = cc.get('help_title_font_size', 50)
help_font_size = cc.get('help_font_size', 20)
help_border_width = cc.get('help_border_width', 3)

popup_top_margin = cc.get('popup_top_margin', 70)
popup_font_size = cc.get('popup_font_size', 24)
popup_color = [arcade.color.WHITE + (255,), arcade.color.BLACK + (255,)]

# how fast the popup will turn transparent
# default is 2, which means a popup will live for
# slightly more than 2 seconds
# 255 / 2 / 60 fps = ~2.1s
popup_alpha_step = cc.get('popup_alpha_step', 2)

theme = cc.get('theme', 0)

bg_color = [arcade.color.SMOKY_BLACK, (163, 178, 207)]
board_color = [(130, 110, 45), (138, 131, 132)]
cell_color = [arcade.color.SMOKY_BLACK, (163, 178, 207)]
cell_alpha = 180
solution_color = arcade.color.RED + (170,)
triangle_color = (255, 187, 0)
triangle_lights_color = [(255, 187, 0), (38, 28, 0)]
wrong_triangle_color = arcade.color.RED
line_color = [(254, 213, 135), (228, 191, 167)]
solved_line_color = (254, 158, 1)
help_font_color = arcade.color.BLACK
help_border_color = arcade.color.WHITE
help_bg_color = arcade.color.ASH_GREY + (230,)
hint_color = arcade.color.GREEN + (100,)

board_width = cc.get('board_width', 4)
board_height = cc.get('board_height', 4)
board_start = cc.get('board_start', [0, 0])
board_exit = cc.get('board_exit', None)     # by default the exit is at the top right corner

hide_triangle_probability = cc.get('hide_triangle_probability', 0.4)
max_paths_generated = cc.get('max_paths_generated', 10000)
generation_time_limit = cc.get('generation_time_limit', 1.0)
obstacles_count = cc.get('obstacles_count', 0)
custom_puzzle_code = cc.get('custom_puzzle_code', None)

menu_vertical_margin = cc.get('menu_vertical_margin', 80)
menu_font_size = cc.get('menu_font_size', 42)
menu_font_color = arcade.color.WHITE
menu_active_color = arcade.color.GREEN
menu_bg_color = (55, 57, 63)
