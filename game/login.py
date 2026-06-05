"""
用户登录界面
游戏启动时的第一个界面，用于用户登录或注册
"""
from tkinter import Frame, Canvas, Entry, Label, messagebox
from game.constants import COLORS, LOGIN_TITLE, LOGIN_BUTTON_TEXT, USER_INFO_LABEL
from game.utils import create_button, create_label
from game.background_fill import fill_background_with_image
from game.user_manager import get_user_manager
from game.toast import show_toast


class Login(Frame):
    """用户登录界面"""

    def __init__(self, root, on_login_success):
        """
        初始化登录界面

        Args:
            root: 父窗口
            on_login_success: 登录成功后的回调函数
        """
        super().__init__(root, bg=COLORS["background"])
        self.on_login_success = on_login_success
        self.user_manager = get_user_manager()
        self._setup_ui()

    def _setup_ui(self):
        """设置UI界面"""
        # 使用背景图片填充
        self._canvas = fill_background_with_image(
            self, "bg_menu.jpeg", COLORS["login_bg"]
        )

        # 创建主容器（用于居中所有内容）
        self.main_container = Frame(self._canvas, bg=COLORS["login_bg"])
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")

        # 标题
        title_label = create_label(
            self.main_container,
            LOGIN_TITLE,
            font_size=36
        )
        # 设置标签背景色
        title_label.config(bg=COLORS["login_bg"])
        title_label.pack(pady=(0, 40))

        # 昵称输入区域
        self._setup_input_area()

        # 绑定回车键
        self.bind("<Return>", lambda e: self._on_login())

    def _setup_input_area(self):
        """设置输入区域"""
        # 输入框容器
        input_frame = Frame(
            self.main_container,
            bg=COLORS["input_bg"],
            highlightbackground=COLORS["input_border"],
            highlightthickness=2,
            relief="solid",
            padx=20,
            pady=20
        )
        input_frame.pack()

        # 输入提示
        input_label = Label(
            input_frame,
            text="请输入昵称:",
            font=("Microsoft YaHei", 14),
            fg=COLORS["text"],
            bg=COLORS["input_bg"]
        )
        input_label.pack(pady=(0, 10))

        # 昵称输入框
        self.nickname_entry = Entry(
            input_frame,
            font=("Microsoft YaHei", 16),
            fg=COLORS["text"],
            bg=COLORS["input_bg"],
            insertbackground=COLORS["text"],
            width=20,
            justify="center"
        )
        self.nickname_entry.pack(pady=(0, 20))
        self.nickname_entry.focus_set()  # 自动聚焦

        # 登录按钮
        login_btn = create_button(
            input_frame,
            LOGIN_BUTTON_TEXT,
            width=20,
            height=2,
            command=self._on_login
        )
        login_btn.pack()

    def _on_login(self):
        """处理登录/注册"""
        nickname = self.nickname_entry.get().strip()

        # 验证昵称长度
        if len(nickname) < 1:
            show_toast("昵称不能为空", self, toast_type="warning")
            return
        if len(nickname) > 50:
            show_toast("昵称不能超过50个字符", self, toast_type="warning")
            return

        # 检查用户是否存在
        if self.user_manager.user_exists(nickname):
            # 用户存在，直接登录
            if self.user_manager.login_user(nickname):
                self.on_login_success()
            else:
                show_toast("登录失败，请重试", self, toast_type="error")
        else:
            # 用户不存在，询问是否创建
            response = messagebox.askyesno(
                "创建新用户",
                f"用户 '{nickname}' 不存在，是否创建新用户？"
            )
            if response:
                if self.user_manager.create_user(nickname):
                    self.on_login_success()
                else:
                    show_toast("创建用户失败，请重试", self, toast_type="error")
            else:
                # 用户取消创建，清空输入框并重新聚焦
                self.nickname_entry.delete(0, 'end')
                self.nickname_entry.focus_set()

    def get_current_nickname(self):
        """获取当前登录的昵称（用于测试）"""
        return self.user_manager.get_current_nickname()