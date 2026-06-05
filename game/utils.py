"""
工具函数
"""

import os
from tkinter import messagebox, Button, Label
from game.constants import COLORS  # 确保constants.py文件存在并包含所需常量
from game.toast import show_toast

# ==================== 图片加载 ====================
_image_cache = {}

def load_image(filename, size=None):
    """
    加载 images/ 目录下的图片，支持缩放。
    返回 PhotoImage 对象，失败返回 None。
    size: (width, height) 或 None
    """
    try:
        from PIL import Image, ImageTk

        # 尝试导入资源工具
        try:
            from game.resource_utils import get_resource_path
            USE_RESOURCE_UTILS = True
        except ImportError:
            USE_RESOURCE_UTILS = False

        key = (filename, size)
        if key not in _image_cache:
            if USE_RESOURCE_UTILS:
                # 打包环境：使用资源工具获取路径
                path = get_resource_path(os.path.join("images", filename))
            else:
                # 开发环境：使用相对路径
                path = os.path.join("images", filename)

            img = Image.open(path)
            if size:
                # 使用BILINEAR而不是LANCZOS，更快但质量稍差
                # 对于背景图片，BILINEAR通常足够好
                img = img.resize(size, Image.BILINEAR)
            photo = ImageTk.PhotoImage(img)
            _image_cache[key] = photo
        return _image_cache[key]
    except Exception as e:
        print(f"[load_image] 加载失败 {filename}: {e}")
        return None


def load_image_fill(filename, target_size):
    """
    加载图片并缩放以填充目标尺寸（保持宽高比，可能裁剪）

    Args:
        filename: 图片文件名
        target_size: (width, height) 目标尺寸

    Returns:
        PhotoImage 对象或 None
    """
    try:
        from PIL import Image, ImageTk
        target_w, target_h = target_size

        # 检查缓存
        key = (filename, target_size, "fill")
        if key not in _image_cache:
            # 尝试导入资源工具
            try:
                from game.resource_utils import get_resource_path
                USE_RESOURCE_UTILS = True
            except ImportError:
                USE_RESOURCE_UTILS = False

            if USE_RESOURCE_UTILS:
                # 打包环境：使用资源工具获取路径
                path = get_resource_path(os.path.join("images", filename))
            else:
                # 开发环境：使用相对路径
                path = os.path.join("images", filename)

            img = Image.open(path)

            # 计算缩放比例以填充目标尺寸
            img_w, img_h = img.size
            width_ratio = target_w / img_w
            height_ratio = target_h / img_h

            # 使用较大的比例以确保填充整个区域
            scale = max(width_ratio, height_ratio)

            # 计算新尺寸
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            # 缩放图片
            img = img.resize((new_w, new_h), Image.BILINEAR)

            # 如果需要，裁剪图片以匹配目标尺寸
            if new_w > target_w or new_h > target_h:
                left = (new_w - target_w) // 2
                top = (new_h - target_h) // 2
                right = left + target_w
                bottom = top + target_h
                img = img.crop((left, top, right, bottom))

            photo = ImageTk.PhotoImage(img)
            _image_cache[key] = photo

        return _image_cache[key]
    except Exception as e:
        print(f"[load_image_fill] 加载失败 {filename}: {e}")
        return None


def create_button(parent, text, width=20, height=2, command=None, bg=None, fg=COLORS["text"]):
    """
    创建按钮
    """
    if bg is None:
        bg = COLORS["button"]

    button = Button(
        parent,
        text=text,
        width=width,
        height=height,
        bg=bg,
        fg=fg,
        activebackground=COLORS.get("button_disabled", "#555555"),  # 兼容无button_disabled的情况
        activeforeground=COLORS["text"],
        font=("Microsoft YaHei", 12),
        command=command
    )
    return button


def show_error(message, parent=None):
    """显示错误消息"""
    show_toast(message, parent, toast_type="error")


def show_info(message, parent=None):
    """显示信息消息"""
    show_toast(message, parent, toast_type="info")


def center_window(window, width, height):
    """
    居中窗口
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_label(parent, text, font_size=14, fg=COLORS["text"]):
    """
    创建标签
    """
    label = Label(
        parent,
        text=text,
        fg=fg,
        bg=COLORS["background"],
        font=("Microsoft YaHei", font_size)
    )
    return label


def create_header_label(parent, text, font_size=24):
    """
    创建标题标签
    """
    label = Label(
        parent,
        text=text,
        fg=COLORS["text"],
        bg=COLORS["background"],
        font=("Microsoft YaHei", font_size, "bold")
    )
    return label


# ==================== 拼音工具函数 ====================

try:
    from pypinyin import lazy_pinyin

    def get_pinyin_initial(name):
        """
        获取拼音首字母

        Args:
            name: 中文名称

        Returns:
            拼音首字母字符串，例如："张三" -> "ZS"
        """
        if not name or not isinstance(name, str):
            return ""
        pinyin_list = lazy_pinyin(name)
        # 提取每个拼音的首字母并大写
        initials = ''.join([p[0].upper() for p in pinyin_list if p])
        return initials

    def get_pinyin_for_sort(name):
        """
        获取用于排序的拼音字符串

        Args:
            name: 中文名称

        Returns:
            完整的拼音字符串，例如："张三" -> "ZHANGSAN"
        """
        if not name or not isinstance(name, str):
            return ""
        pinyin_list = lazy_pinyin(name)
        # 拼接所有拼音并大写
        full_pinyin = ''.join([p.upper() for p in pinyin_list if p])
        return full_pinyin

except ImportError:
    # 如果pypinyin未安装，使用简单回退函数
    def get_pinyin_initial(name):
        """回退函数：返回原始名称"""
        return name if name else ""

    def get_pinyin_for_sort(name):
        """回退函数：返回原始名称"""
        return name if name else ""

    print("警告: pypinyin库未安装，拼音排序功能受限")
