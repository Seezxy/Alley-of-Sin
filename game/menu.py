"""
主菜单界面
"""

from tkinter import Frame, Label, Canvas
from game.constants import COLORS, USER_INFO_LABEL
from game.utils import create_button, create_label, load_image
from game.background_fill import fill_background_with_image
from game.user_manager import get_user_manager
from game.save_crypto import _is_dev_mode


class Menu(Frame):
    """主菜单"""

    def __init__(self, root, on_start, on_inventory=None, on_gacha=None, on_dev_panel=None):
        super().__init__(root, bg=COLORS["background"])
        self.on_start  = on_start
        self.on_inventory = on_inventory  # 背包回调
        self.on_gacha = on_gacha  # 抽奖回调
        self.on_dev_panel = on_dev_panel  # 开发者面板回调
        self._bg_image = None
        self.user_manager = get_user_manager()
        self._setup_ui()

    def _setup_ui(self):
        # 用图片填充整个背景 - 使用原来的bg_menu.jpeg
        # 使用浅灰色作为临时背景色，避免黑色闪烁
        self._canvas = fill_background_with_image(
            self, "bg_menu.jpeg", "#404040"  # 中灰色，比黑色柔和
        )
        self._canvas_img_id = None  # fill_background_with_image不返回image_id

        # 标题
        self._canvas.create_text(0, 0, tags="title",
            text="罪恶巷口", font=("Microsoft YaHei", 48, "bold"),
            fill=COLORS["text"], anchor="center")

        # 用户信息显示区域（右上角）
        self._setup_user_info()

        # 绑定大小调整事件来更新标题位置
        self.bind("<Configure>", self._on_resize)


        # 内容 Frame（使用纯色背景）
        self.content_frame = Frame(
            self,
            bg=COLORS["button"],
            highlightbackground=COLORS["border"],
            highlightthickness=2,
            relief="solid",
            padx=30,
            pady=20
        )
        self.content_frame.place(relx=0.5, rely=0.55, anchor="center")
        content = self.content_frame  # 用于后续引用

        # 内容区域按钮和标签
        from game.utils import create_button, create_label

        btn = create_button(content, "开始游戏", width=25, height=3,
                      command=self._on_start)
        btn.pack(pady=(0, 15))

        # 背包按钮
        if self.on_inventory:
            inventory_btn = create_button(content, "📦 背包", width=20, height=2,
                                  command=self._on_inventory)
            inventory_btn.pack(pady=(0, 10))

        # 抽奖按钮
        if self.on_gacha:
            gacha_btn = create_button(content, "🎰 抽奖", width=20, height=2,
                              command=self._on_gacha)
            gacha_btn.pack(pady=(0, 10))

        # 开发者按钮（仅开发者模式可见）
        if _is_dev_mode() and self.on_dev_panel:
            dev_btn = create_button(content, "🔧 开发者", width=20, height=2,
                              command=self._on_dev_panel)
            dev_btn.pack(pady=(0, 15))

        # 创建标签
        lbl_text = "街头格斗锦标赛\n64 强 → 32 强 → 16 强 → 8 强 → 4 强 → 半决赛 → 决赛 → 冠军"
        lbl = Label(content, text=lbl_text, font=("Microsoft YaHei", 12),
                   fg=COLORS["text"], bg=COLORS["button"], justify="center")
        lbl.pack()

    def _setup_user_info(self):
        """设置用户信息显示区域"""
        # 获取当前用户昵称
        nickname = self.user_manager.get_current_nickname()
        if not nickname:
            nickname = "未登录"

        # 创建用户信息Frame
        self.user_frame = Frame(
            self._canvas,
            bg=COLORS["user_info_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid",
            padx=15,
            pady=8
        )

        # 用户信息标签
        self.user_label = Label(
            self.user_frame,
            text=f"{USER_INFO_LABEL}{nickname}",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text"],
            bg=COLORS["user_info_bg"]
        )
        self.user_label.pack()

        # 货币显示
        currency_amount = self.user_manager.get_currency()
        self.currency_label = Label(
            self.user_frame,
            text=f"💵 {currency_amount}",
            font=("Microsoft YaHei", 12),
            fg=COLORS["highlight"],
            bg=COLORS["user_info_bg"]
        )
        self.currency_label.pack()

        # 将用户信息Frame放置到画布右上角，并添加tag以便调整位置
        self._canvas.create_window(0, 0, window=self.user_frame, anchor="ne", tags="user_info")

    def refresh_user_info(self):
        """刷新用户信息显示"""
        # 获取当前用户昵称
        nickname = self.user_manager.get_current_nickname()
        if not nickname:
            nickname = "未登录"

        # 更新用户信息标签
        self.user_label.config(text=f"{USER_INFO_LABEL}{nickname}")

        # 更新货币显示
        currency_amount = self.user_manager.get_currency()
        self.currency_label.config(text=f"💵 {currency_amount}")

    def _on_resize(self, event):
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return

        # 标题居中在上方 1/3
        self._canvas.coords("title", w / 2, h * 0.28)

        # 更新用户信息区域位置（右上角，留10像素边距）
        user_frame = self._canvas.find_withtag("user_info")
        if user_frame:
            self._canvas.coords(user_frame, w - 10, 10)

    def _on_start(self):
        self.on_start()

    def _on_inventory(self):
        """打开背包界面"""
        if self.on_inventory:
            self.on_inventory()

    def _on_gacha(self):
        """打开抽奖界面"""
        if self.on_gacha:
            self.on_gacha()

    def _on_dev_panel(self):
        """打开开发者面板"""
        if self.on_dev_panel:
            self.on_dev_panel()
