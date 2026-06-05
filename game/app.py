"""
罪恶巷口 - 主入口
"""

import os
import sys
from tkinter import Tk
from game.login import Login
from game.menu import Menu
from game.mode_select import ModeSelect
from game.difficulty_select import DifficultySelect
from game.character_select import CharacterSelect
from game.tournament import Tournament
from game.constants import COLORS
from game.user_manager import get_user_manager

# 尝试导入资源工具
try:
    from game.resource_utils import init_user_data
    HAS_RESOURCE_UTILS = True
except ImportError:
    HAS_RESOURCE_UTILS = False


class Game:

    def __init__(self, root):
        self.root = root
        self.root.title("罪恶巷口")
        self.root.configure(bg=COLORS["background"])

        self.saved_player_attrs = None
        self.dev_player_attrs = None  # 开发者面板设置的自定义属性
        self.selected_difficulty = 1  # 默认标准
        self._is_endless_mode = False  # 无尽模式标记

        # 初始化用户数据目录（如果使用资源工具）
        if HAS_RESOURCE_UTILS:
            try:
                user_data_dir = init_user_data()
                print(f"用户数据目录: {user_data_dir}")
            except Exception as e:
                print(f"初始化用户数据目录失败: {e}")

        # 初始化用户管理器
        self.user_manager = get_user_manager()

        # 创建登录界面（第一个界面）
        self.login = Login(root, self.on_login_success)

        # 其他界面初始为None，延迟创建
        self.menu = None
        self.mode_select = None
        self.difficulty_select = None
        self.character_select = None
        self.tournament = None
        self.endless_mode = None  # 无尽模式界面
        self.inventory_frame = None  # 背包界面
        self.gacha_frame = None  # 抽奖界面
        self.smelting_frame = None  # 熔炼界面

        self.current_frame = None
        self.show_frame(self.login)

    def show_frame(self, frame):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = frame
        frame.pack(expand=True, fill="both")

    def open_dev_panel(self):
        """打开开发者面板"""
        from game.dev_panel import DevPanel
        DevPanel(self.root, self)

    def on_login_success(self):
        """登录成功后的回调"""
        # 创建菜单界面（如果尚未创建）
        if self.menu is None:
            from game.menu import Menu
            self.menu = Menu(self.root, self.on_menu_start,
                           self.show_inventory_from_menu,
                           self.show_gacha_from_menu,
                           self.open_dev_panel)

        # 切换到菜单界面
        self.show_frame(self.menu)

    def on_menu_start(self):
        if self.mode_select is None:
            from game.mode_select import ModeSelect
            self.mode_select = ModeSelect(
                self.root,
                self.on_mode_select,
                self.on_back_to_menu,
                lambda: self.show_inventory(self.mode_select)  # 背包回调
            )
        self.show_frame(self.mode_select)

    def on_mode_select(self, mode):
        if mode == "pve":
            if self.difficulty_select is None:
                from game.difficulty_select import DifficultySelect
                self.difficulty_select = DifficultySelect(
                    self.root,
                    self.on_confirm_difficulty,
                    self.on_back_to_mode_select,
                    lambda: self.show_inventory(self.difficulty_select)  # 背包回调
                )
            self.show_frame(self.difficulty_select)

    def on_confirm_difficulty(self, ai_rewards, is_endless=False):
        self.selected_difficulty = ai_rewards
        self._is_endless_mode = is_endless  # 保存无尽模式标记

        if self.character_select is None:
            from game.character_select import CharacterSelect
            self.character_select = CharacterSelect(
                self.root,
                self.on_confirm_character,
                self.on_back_to_difficulty,
                lambda: self.show_inventory(self.character_select),  # 背包回调
                self.open_dev_panel  # 开发者面板回调
            )
        self.show_frame(self.character_select)

    def on_confirm_character(self, char_key="loulo"):
        # 合并开发者自定义属性到本轮属性
        merged_attrs = self.saved_player_attrs.copy() if self.saved_player_attrs else {}
        if self.dev_player_attrs:
            merged_attrs.update(self.dev_player_attrs)

        if self._is_endless_mode:
            # 无尽模式
            if self.endless_mode is None:
                from game.endless_mode import EndlessMode
                self.endless_mode = EndlessMode(
                    self.root,
                    self.on_back_to_character_select,
                    self.on_back_to_menu
                )
            self.endless_mode.reset(merged_attrs if merged_attrs else None, char_key)
            self.show_frame(self.endless_mode)
        else:
            # 正常锦标赛模式
            if self.tournament is None:
                from game.tournament import Tournament
                self.tournament = Tournament(self.root, self.on_back_to_character_select, self.on_back_to_menu)
            self.tournament.reset(merged_attrs if merged_attrs else None, char_key, self.selected_difficulty)
            self.show_frame(self.tournament)

    def on_back_to_menu(self):
        self.saved_player_attrs = None
        self.dev_player_attrs = None
        self._is_endless_mode = False  # 重置无尽模式标记

        # 确保菜单界面已创建
        if self.menu is None:
            from game.menu import Menu
            self.menu = Menu(self.root, self.on_menu_start)
        # 刷新用户信息显示
        self.menu.refresh_user_info()
        self.show_frame(self.menu)

    def on_back_to_mode_select(self):
        if self.mode_select is None:
            from game.mode_select import ModeSelect
            self.mode_select = ModeSelect(
                self.root,
                self.on_mode_select,
                self.on_back_to_menu,
                lambda: self.show_inventory(self.mode_select)  # 背包回调
            )
        self.show_frame(self.mode_select)

    def on_back_to_difficulty(self):
        if self.difficulty_select is None:
            from game.difficulty_select import DifficultySelect
            self.difficulty_select = DifficultySelect(
                self.root,
                self.on_confirm_difficulty,
                self.on_back_to_mode_select,
                lambda: self.show_inventory(self.difficulty_select)  # 背包回调
            )
        self.show_frame(self.difficulty_select)

    def on_back_to_character_select(self):
        # 重置无尽模式标记
        self._is_endless_mode = False

        if self.character_select is None:
            from game.character_select import CharacterSelect
            self.character_select = CharacterSelect(
                self.root,
                self.on_confirm_character,
                self.on_back_to_difficulty,
                lambda: self.show_inventory(self.character_select),  # 背包回调
                self.open_dev_panel  # 开发者面板回调
            )
        self.show_frame(self.character_select)

    def show_inventory(self, return_to_frame=None):
        """显示背包界面

        Args:
            return_to_frame: 返回时要显示的界面，如果为None则根据当前界面决定
        """
        # 保存当前界面，用于返回
        self.pre_inventory_frame = self.current_frame if return_to_frame is None else return_to_frame

        # 创建背包界面（如果尚未创建）
        if self.inventory_frame is None:
            from game.inventory_frame import InventoryFrame
            self.inventory_frame = InventoryFrame(
                self.root,
                self.on_back_from_inventory,
                self.show_smelting_from_inventory
            )
        else:
            # 只在非首次时刷新（首次在__init__中已构建完整UI）
            self.inventory_frame.refresh_all()

        # 显示背包界面
        self.show_frame(self.inventory_frame)

    def on_back_from_inventory(self):
        """从背包界面返回"""
        if hasattr(self, 'pre_inventory_frame') and self.pre_inventory_frame:
            # 如果返回的是菜单，刷新用户信息
            if self.pre_inventory_frame == self.menu and self.menu:
                self.menu.refresh_user_info()
            self.show_frame(self.pre_inventory_frame)
        else:
            # 默认返回菜单
            self.on_back_to_menu()

    def show_inventory_from_menu(self):
        """从菜单打开背包界面"""
        self.show_inventory(self.menu)

    def show_smelting_from_inventory(self):
        """从背包打开熔炼界面"""
        self.show_smelting(self.inventory_frame)

    def show_smelting(self, return_to_frame=None):
        """显示熔炼界面

        Args:
            return_to_frame: 返回时要显示的界面，如果为None则根据当前界面决定
        """
        # 保存当前界面，用于返回
        self.pre_smelting_frame = self.current_frame if return_to_frame is None else return_to_frame

        # 创建熔炼界面（如果尚未创建）
        if self.smelting_frame is None:
            from game.smelting_frame import SmeltingFrame
            self.smelting_frame = SmeltingFrame(self.root, self.on_back_from_smelting)
        else:
            # 只在非首次时刷新（首次在__init__中已构建完整UI）
            self.smelting_frame.refresh_all()

        # 显示熔炼界面
        self.show_frame(self.smelting_frame)

    def on_back_from_smelting(self):
        """从熔炼界面返回"""
        if hasattr(self, 'pre_smelting_frame') and self.pre_smelting_frame:
            # 如果返回的是背包，刷新背包显示
            if self.pre_smelting_frame == self.inventory_frame and self.inventory_frame:
                self.inventory_frame.refresh_all()
            self.show_frame(self.pre_smelting_frame)
        else:
            # 默认返回菜单
            self.on_back_to_menu()

    def show_gacha_from_menu(self):
        """从菜单打开抽奖界面"""
        # 保存当前界面，用于返回
        self.pre_gacha_frame = self.current_frame

        # 创建抽奖界面（如果尚未创建）
        if self.gacha_frame is None:
            from game.gacha_frame import GachaFrame
            self.gacha_frame = GachaFrame(self.root, self.on_back_from_gacha)
        else:
            # 只在非首次时刷新（首次在__init__中已构建完整UI）
            self.gacha_frame.refresh_all()

        # 显示抽奖界面
        self.show_frame(self.gacha_frame)

    def on_back_from_gacha(self):
        """从抽奖界面返回"""
        if hasattr(self, 'pre_gacha_frame') and self.pre_gacha_frame:
            # 如果返回的是菜单，刷新用户信息
            if self.pre_gacha_frame == self.menu and self.menu:
                self.menu.refresh_user_info()
            # 如果返回的是背包，刷新背包显示
            elif self.pre_gacha_frame == self.inventory_frame and self.inventory_frame:
                self.inventory_frame.refresh_all()
            self.show_frame(self.pre_gacha_frame)
        else:
            # 默认返回菜单
            self.on_back_to_menu()


def main():
    root = Tk()
    root.geometry("900x700")
    root.state('zoomed')
    root.resizable(True, True)
    game = Game(root)
    root.mainloop()
    

if __name__ == "__main__":
    main()
