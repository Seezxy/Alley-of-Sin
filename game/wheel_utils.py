"""
鼠标滚轮工具函数
提供统一的滚轮绑定功能
"""

import tkinter as tk
from typing import Callable, Optional


def bind_mouse_wheel(widget, target_widget: Optional[tk.Widget] = None):
    """
    绑定鼠标滚轮到widget及其所有子widget

    Args:
        widget: 要绑定滚轮事件的widget
        target_widget: 实际接收滚轮事件的widget（通常是Canvas），如果为None则使用widget本身
    """
    if target_widget is None:
        target_widget = widget

    # 使用事件标记来防止重复处理
    last_event_time = 0
    event_threshold = 50  # 毫秒，防止同一事件被多次处理

    def _on_mouse_wheel(event):
        nonlocal last_event_time

        # 防止同一事件被多次处理
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        if current_time - last_event_time < event_threshold:
            return "break"  # 停止事件传播

        last_event_time = current_time

        # Windows和Mac的滚轮事件不同
        if event.num == 5 or event.delta == -120:  # 向下滚动
            target_widget.yview_scroll(3, "units")  # 改为三倍距离
        elif event.num == 4 or event.delta == 120:   # 向上滚动
            target_widget.yview_scroll(-3, "units")  # 改为三倍距离

        return "break"  # 停止事件传播，防止被其他widget处理

    # 绑定各种滚轮事件到widget本身
    widget.bind("<MouseWheel>", _on_mouse_wheel, add='+')      # Windows
    widget.bind("<Button-4>", _on_mouse_wheel, add='+')        # Linux向上
    widget.bind("<Button-5>", _on_mouse_wheel, add='+')        # Linux向下

    # 为所有现有和未来的子widget绑定滚轮事件
    # 使用add='+'确保不覆盖现有的事件绑定
    def _bind_to_children(parent):
        for child in parent.winfo_children():
            # 绑定滚轮事件，使用add='+'确保不覆盖其他事件
            child.bind("<MouseWheel>", _on_mouse_wheel, add='+')
            child.bind("<Button-4>", _on_mouse_wheel, add='+')
            child.bind("<Button-5>", _on_mouse_wheel, add='+')
            _bind_to_children(child)

    _bind_to_children(widget)

    # 监听新的子widget创建
    def _on_child_configure(event):
        _bind_to_children(widget)

    widget.bind("<Configure>", _on_child_configure, add='+')

    return widget


def bind_mouse_wheel_to_canvas(canvas: tk.Canvas, content_frame: tk.Frame):
    """
    为Canvas和其内容Frame绑定滚轮事件

    Args:
        canvas: 包含滚动内容的Canvas
        content_frame: Canvas内部的Frame
    """
    # 使用事件标记来防止重复处理
    last_event_time = 0
    event_threshold = 50  # 毫秒，防止同一事件被多次处理

    def _on_mouse_wheel(event):
        nonlocal last_event_time

        # 防止同一事件被多次处理
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        if current_time - last_event_time < event_threshold:
            return "break"  # 停止事件传播

        last_event_time = current_time


        # 使用单位值，增加滚动倍数
        scroll_units = 6  # 每次滚动6个单位（原来的两倍）

        if event.num == 5 or event.delta == -120:  # 向下滚动
            canvas.yview_scroll(scroll_units, "units")  # 增加滚动倍数
        elif event.num == 4 or event.delta == 120:   # 向上滚动
            canvas.yview_scroll(-scroll_units, "units")  # 增加滚动倍数

        return "break"  # 停止事件传播，防止被其他widget处理

    # 绑定到Canvas
    canvas.bind("<MouseWheel>", _on_mouse_wheel, add='+')
    canvas.bind("<Button-4>", _on_mouse_wheel, add='+')
    canvas.bind("<Button-5>", _on_mouse_wheel, add='+')

    # 绑定到内容Frame及其所有子widget
    def _bind_to_frame_and_children(parent):
        parent.bind("<MouseWheel>", _on_mouse_wheel, add='+')
        parent.bind("<Button-4>", _on_mouse_wheel, add='+')
        parent.bind("<Button-5>", _on_mouse_wheel, add='+')

        for child in parent.winfo_children():
            _bind_to_frame_and_children(child)

    _bind_to_frame_and_children(content_frame)

    # 监听内容Frame的新子widget创建
    def _on_frame_child_configure(event):
        _bind_to_frame_and_children(content_frame)

    content_frame.bind("<Configure>", _on_frame_child_configure, add='+')

    return canvas


def bind_mouse_wheel_to_text(text_widget: tk.Text):
    """
    为Text组件绑定滚轮事件

    Args:
        text_widget: Text组件
    """
    # 使用事件标记来防止重复处理
    last_event_time = 0
    event_threshold = 50  # 毫秒，防止同一事件被多次处理

    def _on_mouse_wheel(event):
        nonlocal last_event_time

        # 防止同一事件被多次处理
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        if current_time - last_event_time < event_threshold:
            return "break"  # 停止事件传播

        last_event_time = current_time

        # Windows和Mac的滚轮事件不同
        if event.num == 5 or event.delta == -120:  # 向下滚动
            text_widget.yview_scroll(3, "units")  # 改为三倍距离
        elif event.num == 4 or event.delta == 120:   # 向上滚动
            text_widget.yview_scroll(-3, "units")  # 改为三倍距离

        return "break"  # 停止事件传播，防止被其他widget处理

    # 绑定到Text组件本身
    text_widget.bind("<MouseWheel>", _on_mouse_wheel, add='+')
    text_widget.bind("<Button-4>", _on_mouse_wheel, add='+')
    text_widget.bind("<Button-5>", _on_mouse_wheel, add='+')

    return text_widget


def bind_mouse_wheel_to_widget_for_canvas(widget, canvas: tk.Canvas):
    """
    为widget绑定滚轮事件，滚动指定的Canvas

    Args:
        widget: 要绑定滚轮事件的widget
        canvas: 要滚动的Canvas
    """
    # 使用事件标记来防止重复处理
    last_event_time = 0
    event_threshold = 50  # 毫秒，防止同一事件被多次处理

    def _on_mouse_wheel(event):
        nonlocal last_event_time

        # 防止同一事件被多次处理
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        if current_time - last_event_time < event_threshold:
            return "break"  # 停止事件传播

        last_event_time = current_time


        # 使用单位值，增加滚动倍数
        scroll_units = 6  # 每次滚动6个单位（原来的两倍）

        if event.num == 5 or event.delta == -120:  # 向下滚动
            canvas.yview_scroll(scroll_units, "units")  # 增加滚动倍数
        elif event.num == 4 or event.delta == 120:   # 向上滚动
            canvas.yview_scroll(-scroll_units, "units")  # 增加滚动倍数

        return "break"  # 停止事件传播，防止被其他widget处理

    # 绑定滚轮事件，使用add='+'确保不覆盖其他事件
    widget.bind("<MouseWheel>", _on_mouse_wheel, add='+')
    widget.bind("<Button-4>", _on_mouse_wheel, add='+')
    widget.bind("<Button-5>", _on_mouse_wheel, add='+')

    return widget