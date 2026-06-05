"""Allow running the game via `python -m game`."""
from game.app import Game
from tkinter import Tk


def main():
    root = Tk()
    app = Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
