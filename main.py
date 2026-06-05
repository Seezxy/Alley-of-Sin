"""
罪恶巷口 (Sin Alley) - 主入口
街头格斗锦标赛卡牌游戏。从 64 强一路打到冠军。
"""

from tkinter import Tk
from game.app import Game


def main():
    root = Tk()
    root.geometry("900x700")
    root.state("zoomed")
    root.resizable(True, True)
    app = Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
