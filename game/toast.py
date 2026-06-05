"""
淡出提示框工具类
用于显示短暂提示信息并自动淡出
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple
import time

from game.constants import COLORS


class Toast:
    """淡出提示框类"""

    def __init__(self, parent):
        """
        初始化Toast

        Args:
            parent: 父窗口或Frame
        """
        self.parent = parent
        self.toast_window = None
        self.fade_out_id = None

    def show(self, message: str, duration: int = 2000,
             toast_type: str = "info", position: str = "center"):
        """
        显示Toast提示

        Args:
            message: 提示消息
            duration: 显示持续时间（毫秒）
            toast_type: 提示类型，可选值: "info", "success", "warning", "error"
            position: 显示位置，可选值: "center", "top", "bottom"
        """
        # 如果已有Toast正在显示，先关闭它
        if self.toast_window and self.toast_window.winfo_exists():
            self._cancel_fade_out()
            self.toast_window.destroy()

        # 创建Toast窗口
        self.toast_window = tk.Toplevel(self.parent)
        self.toast_window.overrideredirect(True)  # 无边框
        self.toast_window.configure(bg=self._get_bg_color(toast_type))

        # 设置透明度
        self.toast_window.attributes("-alpha", 0.0)

        # 创建消息标签
        label = tk.Label(
            self.toast_window,
            text=message,
            font=("Microsoft YaHei", 11),
            fg=COLORS["text"],
            bg=self._get_bg_color(toast_type),
            padx=20,
            pady=10,
            wraplength=300
        )
        label.pack()

        # 计算位置
        self._position_toast(position)

        # 淡入效果
        self._fade_in(duration)

    def _get_bg_color(self, toast_type: str) -> str:
        """根据提示类型获取背景颜色"""
        color_map = {
            "info": COLORS["info"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"]
        }
        return color_map.get(toast_type, COLORS["info"])

    def _position_toast(self, position: str):
        """定位Toast窗口"""
        # 获取父窗口信息
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # 获取Toast窗口大小
        self.toast_window.update_idletasks()
        toast_width = self.toast_window.winfo_width()
        toast_height = self.toast_window.winfo_height()

        # 计算位置
        if position == "top":
            x = parent_x + (parent_width - toast_width) // 2
            y = parent_y + 20
        elif position == "bottom":
            x = parent_x + (parent_width - toast_width) // 2
            y = parent_y + parent_height - toast_height - 20
        else:  # center
            x = parent_x + (parent_width - toast_width) // 2
            y = parent_y + (parent_height - toast_height) // 2

        # 设置位置
        self.toast_window.geometry(f"+{x}+{y}")

    def _fade_in(self, duration: int):
        """淡入效果"""
        def fade_in_step(alpha: float = 0.0):
            if alpha < 1.0:
                self.toast_window.attributes("-alpha", alpha)
                self.toast_window.after(10, fade_in_step, alpha + 0.05)
            else:
                self.toast_window.attributes("-alpha", 1.0)
                # 淡入完成后开始淡出倒计时
                self.toast_window.after(duration, self._fade_out)

        fade_in_step()

    def _fade_out(self):
        """淡出效果"""
        def fade_out_step(alpha: float = 1.0):
            if alpha > 0.0:
                self.toast_window.attributes("-alpha", alpha)
                self.fade_out_id = self.toast_window.after(10, fade_out_step, alpha - 0.05)
            else:
                self.toast_window.destroy()
                self.toast_window = None
                self.fade_out_id = None

        fade_out_step()

    def _cancel_fade_out(self):
        """取消淡出计时器"""
        if self.fade_out_id:
            self.toast_window.after_cancel(self.fade_out_id)
            self.fade_out_id = None


# 全局Toast管理器
_toast_manager = None

def get_toast_manager(parent=None) -> Toast:
    """
    获取Toast管理器实例

    Args:
        parent: 父窗口，如果为None则使用默认父窗口

    Returns:
        Toast实例
    """
    global _toast_manager
    if _toast_manager is None and parent is not None:
        _toast_manager = Toast(parent)
    return _toast_manager

def show_toast(message: str, parent=None, **kwargs):
    """
    显示Toast提示（便捷函数）

    Args:
        message: 提示消息
        parent: 父窗口
        **kwargs: 传递给Toast.show的其他参数
    """
    if parent is None:
        # 尝试获取活动窗口
        import sys
        if 'tkinter' in sys.modules:
            import tkinter as tk
            parent = tk._default_root
            if parent is None:
                return

    toast = get_toast_manager(parent)
    if toast:
        toast.show(message, **kwargs)