import turtle
import tkinter as tk
from game_manager import GameManager

def main():
    screen = turtle.Screen()
    canvas = screen.getcanvas()
    root = canvas.master

    modes = ["Learn Shapes", "Test Shapes", "Learn Colors", "Test Colors"]
    selected_mode = tk.StringVar(root)
    selected_mode.set(modes[0])

    gm = GameManager()

    def on_mode_change(selection):
        gm.switch_mode(selection)

    opt_menu = tk.OptionMenu(root, selected_mode, *modes, command=on_mode_change)
    opt_menu.pack(side=tk.TOP)

    gm.switch_mode(selected_mode.get())
    screen.mainloop()

if __name__ == "__main__":
    main()
