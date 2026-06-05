"""
模式选择界面
"""

from tkinter import Frame
from game.constants import COLORS
from game.utils import create_button, create_header_label
from game.background_fill import fill_background_with_image


class ModeSelect(Frame):
    """模式选择"""

    def __init__(self, root, on_mode_select, on_back, on_inventory=None):
        super().__init__(root, bg=COLORS["background"])
        self.on_mode_select = on_mode_select
        self.on_back = on_back
        self.on_inventory = on_inventory  # 背包回调
        self._canvas = None
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        # 添加背景图片
        self._canvas = fill_background_with_image(
            self, "bg_menu.jpeg", "#404040"  # 中灰色，避免黑色闪烁
        )

        # 标题
        title = create_header_label(self, "选择游戏模式", font_size=36)
        title.pack(pady=(100, 80))

        # 人机对战按钮
        pve_button = create_button(
            self, "人机对战", width=25, height=3,
            command=lambda: self.on_mode_select("pve")
        )
        pve_button.pack(pady=20)

        # 匹配对战/好友对战（禁用）
        pvp_button = create_button(
            self, "匹配对战 / 好友对战", width=25, height=3
        )
        pvp_button.pack(pady=20)
        pvp_button.config(state="disabled")

        # 返回按钮
        back_button = create_button(
            self, "返回", width=15, height=2, command=self.on_back
        )
        back_button.pack(pady=30)

        # 左下角背包按钮
        self._add_inventory_button()

    def _add_inventory_button(self):
        """在左下角添加背包按钮"""
        inventory_button = create_button(
            self, "背包", width=10, height=2,
            command=self._on_inventory
        )
        # 放置在左下角
        inventory_button.place(relx=0.02, rely=0.95, anchor="sw")

    def _on_inventory(self):
        """打开背包界面"""
        if self.on_inventory:
            self.on_inventory()
        else:
            # 回退到旧方法（打开新窗口）
            # 导入放在这里避免循环导入
            from game.item_ui import InventoryWindow

            # 创建背包窗口
            inventory_window = InventoryWindow(self.master)
            inventory_window.grab_set()  # 模态窗口

