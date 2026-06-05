"""
难度选择界面
"""

from tkinter import Frame, Label
from game.constants import COLORS
from game.utils import create_button, create_header_label, create_label
from game.background_fill import fill_background_with_image

DIFFICULTIES = [
    {"key": "easy",   "name": "简单",   "ai_rewards": 0, "desc": "电脑每轮不获得强化，适合新手"},
    {"key": "normal", "name": "标准",   "ai_rewards": 1, "desc": "电脑每轮随机获得 1 项强化"},
    {"key": "hard",   "name": "困难",   "ai_rewards": 2, "desc": "电脑每轮随机获得 2 项强化"},
    {"key": "hell",   "name": "地狱",   "ai_rewards": 3, "desc": "电脑每轮随机获得 3 项强化，祝你好运"},
    {"key": "endless","name": "无尽",   "ai_rewards": 3, "desc": "地狱难度，无限连续战斗，奖金翻倍"},
]

DIFFICULTY_COLORS = {
    "easy":   COLORS["success"],
    "normal": COLORS["info"],
    "hard":   COLORS["warning"],
    "hell":   COLORS["danger"],
    "endless": COLORS["highlight"],
}


class DifficultySelect(Frame):

    def __init__(self, root, on_confirm, on_back, on_inventory=None):
        super().__init__(root, bg=COLORS["background"])
        self.on_confirm = on_confirm
        self.on_back    = on_back
        self.on_inventory = on_inventory  # 背包回调
        self._canvas = None
        self._setup_ui()

    def _setup_ui(self):
        # 添加背景图片
        self._canvas = fill_background_with_image(
            self, "bg_menu.jpeg", "#404040"  # 中灰色，避免黑色闪烁
        )

        create_header_label(self, "选择难度", font_size=36).pack(pady=(50, 30))

        # 创建难度按钮容器（横排）
        difficulty_frame = Frame(self, bg=COLORS["background"])
        difficulty_frame.pack(pady=20)

        # 创建描述标签容器
        desc_frame = Frame(self, bg=COLORS["background"])
        desc_frame.pack(pady=10)

        # 存储当前选中的难度描述标签
        self.current_desc_label = None

        for i, d in enumerate(DIFFICULTIES):
            color = DIFFICULTY_COLORS[d["key"]]

            # 创建难度按钮
            btn_frame = Frame(difficulty_frame, bg=COLORS["background"])
            btn_frame.pack(side="left", padx=10)

            btn = create_button(btn_frame, d["name"], width=15, height=3,
                                bg=color, command=lambda d=d: self._on_difficulty_select(d))
            btn.pack()

            # 为每个按钮创建对应的描述标签（初始隐藏）
            desc_label = Label(desc_frame, text=d["desc"], bg=COLORS["background"],
                              fg=COLORS["text_secondary"], font=("微软雅黑", 11), wraplength=600)
            desc_label.pack_forget()  # 初始隐藏

            # 将按钮和描述标签关联起来
            btn.desc_label = desc_label
            btn.difficulty_data = d

        # 返回按钮放在下方
        create_button(self, "返回", width=15, height=2,
                      command=self.on_back).pack(pady=30)

        # 左下角背包按钮
        self._add_inventory_button()

    def _add_inventory_button(self):
        """在左下角添加背包按钮"""
        from game.utils import create_button
        inventory_button = create_button(
            self, "背包", width=10, height=2,
            command=self._on_inventory
        )
        # 放置在左下角
        inventory_button.place(relx=0.02, rely=0.95, anchor="sw")

    def _on_difficulty_select(self, difficulty_data):
        """难度选择处理"""
        # 隐藏之前的描述标签
        if self.current_desc_label:
            self.current_desc_label.pack_forget()

        # 显示当前选择的难度描述
        for widget in self.winfo_children():
            if hasattr(widget, 'desc_label') and hasattr(widget, 'difficulty_data'):
                if widget.difficulty_data["key"] == difficulty_data["key"]:
                    widget.desc_label.pack()
                    self.current_desc_label = widget.desc_label
                    # 高亮显示描述
                    widget.desc_label.config(fg=COLORS["highlight"], font=("微软雅黑", 12, "bold"))
                    break

        # 不自动跳转，让用户点击确认按钮
        # 创建确认按钮（如果不存在）
        if not hasattr(self, 'confirm_button') or self.confirm_button is None:
            self.confirm_button = create_button(
                self, f"确认选择：{difficulty_data['name']}", width=25, height=2,
                bg=DIFFICULTY_COLORS[difficulty_data["key"]],
                command=lambda: self.on_confirm(difficulty_data["ai_rewards"], difficulty_data["key"] == "endless")
            )
            self.confirm_button.pack(pady=20)
        else:
            # 更新确认按钮
            self.confirm_button.config(
                text=f"确认选择：{difficulty_data['name']}",
                bg=DIFFICULTY_COLORS[difficulty_data["key"]],
                command=lambda: self.on_confirm(difficulty_data["ai_rewards"], difficulty_data["key"] == "endless")
            )

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
