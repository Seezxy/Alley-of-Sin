"""
背景填充工具
为各个界面提供背景图片填充功能
"""

from tkinter import Canvas, Frame
from game.utils import load_image, load_image_fill
from game.constants import COLORS

def fill_background_with_image(parent, image_name, bg_color=None):
    """
    用图片填充父容器的背景

    Args:
        parent: 父容器（Frame等）
        image_name: 图片文件名
        bg_color: 备用背景颜色（如果图片加载失败）

    Returns:
        Canvas对象（用于后续调整图片）
    """
    bg_color = bg_color or COLORS["background"]

    # 创建Canvas覆盖整个父容器
    canvas = Canvas(parent, highlightthickness=0, bd=0, bg=bg_color)
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    # 立即加载默认尺寸的图片（800x600）
    default_bg_image = load_image(image_name, (800, 600))
    image_id = None

    if default_bg_image:
        image_id = canvas.create_image(0, 0, anchor="nw", image=default_bg_image)
        canvas.image = default_bg_image  # 保持引用

    # 当父容器尺寸确定时，更新为正确尺寸的图片
    def update_to_correct_size():
        nonlocal image_id

        w = parent.winfo_width()
        h = parent.winfo_height()

        if w < 10 or h < 10:
            # 尺寸太小，稍后重试
            parent.after(10, update_to_correct_size)
            return

        # 加载正确尺寸的图片
        correct_bg_image = load_image(image_name, (w, h))
        if correct_bg_image:
            if image_id:
                # 更新现有图片
                canvas.itemconfig(image_id, image=correct_bg_image)
            else:
                # 创建新图片
                image_id = canvas.create_image(0, 0, anchor="nw", image=correct_bg_image)
            canvas.image = correct_bg_image  # 更新引用

    # 开始更新到正确尺寸
    update_to_correct_size()

    return canvas

def fill_background_with_resizable_image(parent, image_name, bg_color=None):
    """
    用可调整大小的图片填充父容器的背景

    Args:
        parent: 父容器（Frame等）
        image_name: 图片文件名
        bg_color: 备用背景颜色（如果图片加载失败）

    Returns:
        (canvas, image_id) 元组
    """
    bg_color = bg_color or COLORS["background"]

    canvas = Canvas(parent, highlightthickness=0, bd=0, bg=bg_color)
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    image_id = None
    bg_image = None

    def update_background(event=None):
        nonlocal image_id, bg_image

        # 获取父容器尺寸
        w = parent.winfo_width()
        h = parent.winfo_height()

        # 如果尺寸太小，使用窗口的请求尺寸或默认尺寸
        if w < 10 or h < 10:
            # 尝试获取请求的尺寸
            w = parent.winfo_reqwidth()
            h = parent.winfo_reqheight()

            # 如果请求尺寸也小，使用默认尺寸
            if w < 10 or h < 10:
                w, h = 800, 600

        # 加载适应尺寸的图片
        img = load_image(image_name, (w, h))
        if img:
            bg_image = img
            if image_id:
                canvas.itemconfig(image_id, image=img)
            else:
                image_id = canvas.create_image(0, 0, anchor="nw", image=img)
                canvas.tag_lower(image_id)
        elif not image_id:
            # 创建纯色背景
            image_id = canvas.create_rectangle(0, 0, w, h, fill=bg_color, outline="")
            canvas.tag_lower(image_id)

    # 绑定大小调整事件
    parent.bind("<Configure>", update_background)

    # 立即更新一次
    update_background()

    return canvas, image_id

def create_panel_with_background(parent, image_name=None, **kwargs):
    """
    创建带有背景图片的面板

    Args:
        parent: 父容器
        image_name: 背景图片文件名（如果为None则使用纯色背景）
        **kwargs: 传递给Frame的其他参数

    Returns:
        (frame, canvas) 元组
    """
    # 创建Frame
    frame = Frame(parent, **kwargs)

    # 添加背景
    canvas = fill_background_with_image(frame, image_name, frame.cget("bg"))

    return frame, canvas

def create_card_with_background(parent, image_name=None, **kwargs):
    """
    创建带有背景图片的卡片

    Args:
        parent: 父容器
        image_name: 背景图片文件名（如果为None则使用纯色背景）
        **kwargs: 传递给Frame的其他参数

    Returns:
        (frame, canvas) 元组
    """
    # 设置默认样式
    defaults = {
        "bg": COLORS["background"],
        "highlightbackground": COLORS["border"],
        "highlightthickness": 2,
        "relief": "solid",
        "padx": 20,
        "pady": 15,
    }

    # 合并默认值和用户提供的参数
    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value

    return create_panel_with_background(parent, image_name, **kwargs)