"""
熔炼界面模块（Frame版本）
负责熔炼界面的显示和交互，作为Frame嵌入主窗口
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any

from game.constants import (
    COLORS, RARITY_COLORS, ITEM_TYPES, ATTRIBUTE_DISPLAY_NAMES
)
from game.smelting_manager import get_smelting_manager
from game.inventory import get_inventory_manager
from game.item_manager import get_item_manager
from game.wheel_utils import bind_mouse_wheel_to_canvas
from game.toast import show_toast
from game.attribute_utils import get_attribute_utils


class SmeltingFrame(tk.Frame):
    """熔炼界面（Frame版本）"""

    def __init__(self, parent, on_back):
        super().__init__(parent, bg=COLORS["background"])
        self.on_back = on_back  # 返回回调函数

        # 获取管理器实例
        self.smelting_manager = get_smelting_manager()
        self.inventory_manager = get_inventory_manager()
        self.item_manager = get_item_manager()

        # 界面组件
        self.options_frame = None
        self.info_frame = None
        self.selected_option = None
        self.selected_items_count = 0
        self.smelt_count = 1  # 熔炼次数
        self.max_smelt_count = 1  # 最大可熔炼次数

        self._setup_ui()

    def _setup_ui(self):
        """设置界面布局"""
        # 主容器
        main_container = tk.Frame(self, bg=COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题和返回按钮
        header_frame = tk.Frame(main_container, bg=COLORS["background"])
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # 返回按钮
        back_button = tk.Button(
            header_frame,
            text="← 返回",
            font=("Microsoft YaHei", 12),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=self.on_back
        )
        back_button.pack(side=tk.LEFT)

        # 标题
        title_label = tk.Label(
            header_frame,
            text="装 备 熔 炼",
            font=("Microsoft YaHei", 24, "bold"),
            fg=COLORS["warning"],
            bg=COLORS["background"]
        )
        title_label.pack(side=tk.LEFT, padx=(20, 0))

        # 说明文字
        description = tk.Label(
            main_container,
            text="100件低级装备可以合成一件高一级的装备（最高神话）\n选择随机类别可以打八折（80件合一件）",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text_secondary"],
            bg=COLORS["background"],
            justify=tk.CENTER
        )
        description.pack(pady=(0, 20))

        # 内容区域（左右布局）
        content_frame = tk.Frame(main_container, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：熔炼选项区域
        left_frame = tk.Frame(content_frame, bg=COLORS["background"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 熔炼选项标题
        options_label = tk.Label(
            left_frame,
            text="熔 炼 选 项",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        options_label.pack(anchor=tk.W, pady=(0, 10))

        # 熔炼选项面板
        self.options_frame = tk.Frame(
            left_frame,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid"
        )
        self.options_frame.pack(fill=tk.BOTH, expand=True)

        # 右侧：详细信息区域
        right_frame = tk.Frame(content_frame, bg=COLORS["background"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 详细信息标题
        info_label = tk.Label(
            right_frame,
            text="详 细 信 息",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        info_label.pack(anchor=tk.W, pady=(0, 10))

        # 详细信息面板
        self.info_frame = tk.Frame(
            right_frame,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid",
            height=400
        )
        self.info_frame.pack(fill=tk.BOTH, expand=True)
        self.info_frame.pack_propagate(False)  # 固定高度

        # 底部按钮区域
        button_frame = tk.Frame(main_container, bg=COLORS["background"])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 次数控制区域（居中）
        count_control_frame = tk.Frame(button_frame, bg=COLORS["background"])
        count_control_frame.pack(expand=True)

        # 减少按钮
        self.count_minus_btn = tk.Button(
            count_control_frame,
            text="−",
            font=("Microsoft YaHei", 14, "bold"),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            width=3,
            command=self._decrease_count
        )
        self.count_minus_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.count_minus_btn.config(state="disabled")

        # 次数显示
        self.count_label = tk.Label(
            count_control_frame,
            text="1",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["highlight"],
            bg=COLORS["background"],
            width=4
        )
        self.count_label.pack(side=tk.LEFT)

        # 增加按钮
        self.count_plus_btn = tk.Button(
            count_control_frame,
            text="+",
            font=("Microsoft YaHei", 14, "bold"),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            width=3,
            command=self._increase_count
        )
        self.count_plus_btn.pack(side=tk.LEFT, padx=(8, 15))
        self.count_plus_btn.config(state="disabled")

        # 最大按钮
        self.count_max_btn = tk.Button(
            count_control_frame,
            text="最大",
            font=("Microsoft YaHei", 10),
            bg=COLORS["info"],
            fg=COLORS["text"],
            activebackground=COLORS["info_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=self._set_max_count
        )
        self.count_max_btn.pack(side=tk.LEFT, padx=(0, 15))
        self.count_max_btn.config(state="disabled")

        # 熔炼按钮
        self.smelt_btn = tk.Button(
            count_control_frame,
            text="开始熔炼",
            font=("Microsoft YaHei", 14, "bold"),
            bg=COLORS["success"],
            fg=COLORS["text"],
            activebackground=COLORS["success_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=self._smelt_items,
            width=22,
            height=2
        )
        self.smelt_btn.pack(side=tk.LEFT)
        self.smelt_btn.config(state="disabled")

        # 初始显示
        self._refresh_options()
        self._show_default_info()

    def _refresh_options(self):
        """刷新熔炼选项"""
        # 清空选项区域
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # 获取熔炼选项
        options = self.smelting_manager.get_smelting_options()

        if not options:
            # 显示无可用选项
            empty_label = tk.Label(
                self.options_frame,
                text="暂无可用熔炼选项\n请收集更多装备",
                font=("Microsoft YaHei", 14),
                fg=COLORS["text_muted"],
                bg=COLORS["panel_bg"]
            )
            empty_label.pack(expand=True)
            return

        # 创建滚动区域
        canvas = tk.Canvas(
            self.options_frame,
            bg=COLORS["panel_bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.options_frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg=COLORS["panel_bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_canvas(canvas, scrollable_frame)

        # 显示选项 - 使用更大的选项框
        for i, option in enumerate(options):
            option_frame = self._create_option_display(scrollable_frame, option)
            option_frame.pack(fill=tk.X, padx=10, pady=8, ipady=5)  # 增加内边距和外边距

        # 放置滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_option_display(self, parent, option: Dict[str, Any]) -> tk.Frame:
        """创建熔炼选项显示 - 改进版，更大的点击区域"""
        current_rarity = option["current_rarity"]
        next_rarity = option["next_rarity"]
        eq_type = option["type"]
        is_random = option["is_random"]
        required_count = option["required_count"]
        display_name = option["display_name"]

        # 获取稀有度颜色
        current_color = RARITY_COLORS.get(current_rarity, COLORS["text"])
        next_color = RARITY_COLORS.get(next_rarity, COLORS["text"])

        # 选项框架 - 更大的点击区域
        option_frame = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=2,
            relief="solid",
            cursor="hand2"
        )
        option_frame.pack_propagate(False)
        option_frame.config(height=100)  # 增加高度

        # 绑定点击事件到整个框架
        option_frame.bind("<Button-1>", lambda e, o=option: self._select_option(o))

        # 存储选项信息，用于更新选中状态
        option_frame.option_data = option

        # 使用网格布局，让内容居中
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_columnconfigure(1, weight=3)
        option_frame.grid_columnconfigure(2, weight=1)

        # 左侧：稀有度图标和名称
        left_frame = tk.Frame(option_frame, bg=COLORS["card_bg"])
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 当前稀有度
        current_rarity_label = tk.Label(
            left_frame,
            text=current_rarity.upper(),
            font=("Microsoft YaHei", 11, "bold"),
            fg=current_color,
            bg=COLORS["card_bg"]
        )
        current_rarity_label.pack()

        # 箭头
        arrow_label = tk.Label(
            left_frame,
            text="↓",
            font=("Microsoft YaHei", 14),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        arrow_label.pack()

        # 下一稀有度
        next_rarity_label = tk.Label(
            left_frame,
            text=next_rarity.upper(),
            font=("Microsoft YaHei", 11, "bold"),
            fg=next_color,
            bg=COLORS["card_bg"]
        )
        next_rarity_label.pack()

        # 中间：详细信息
        middle_frame = tk.Frame(option_frame, bg=COLORS["card_bg"])
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # 显示名称
        name_label = tk.Label(
            middle_frame,
            text=display_name,
            font=("Microsoft YaHei", 13, "bold"),
            fg=COLORS["text"],
            bg=COLORS["card_bg"],
            anchor="w"
        )
        name_label.pack(anchor="w")

        # 类型信息
        if is_random:
            type_text = "随机类型 (八折优惠)"
            type_color = COLORS["highlight"]
        else:
            type_display = ITEM_TYPES.get(eq_type, eq_type)
            type_text = f"类型: {type_display}"
            type_color = COLORS["text_secondary"]

        type_label = tk.Label(
            middle_frame,
            text=type_text,
            font=("Microsoft YaHei", 11),
            fg=type_color,
            bg=COLORS["card_bg"],
            anchor="w"
        )
        type_label.pack(anchor="w", pady=(5, 0))

        # 右侧：所需数量
        right_frame = tk.Frame(option_frame, bg=COLORS["card_bg"])
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        count_label = tk.Label(
            right_frame,
            text=f"需要: {required_count}件",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["warning"],
            bg=COLORS["card_bg"]
        )
        count_label.pack()

        # 获取可用数量（从预计算缓存中，不需要遍历背包）
        available_count = option.get("available_count", 0)

        available_label = tk.Label(
            right_frame,
            text=f"可用: {available_count}件",
            font=("Microsoft YaHei", 11),
            fg=COLORS["success"] if available_count >= required_count else COLORS["danger"],
            bg=COLORS["card_bg"]
        )
        available_label.pack(pady=(5, 0))

        # 绑定点击事件到所有子组件
        for widget in [left_frame, middle_frame, right_frame,
                      current_rarity_label, arrow_label, next_rarity_label,
                      name_label, type_label, count_label, available_label]:
            widget.bind("<Button-1>", lambda e, o=option: self._select_option(o))
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    child.bind("<Button-1>", lambda e, o=option: self._select_option(o))

        return option_frame

    def _select_option(self, option: Dict[str, Any]):
        """选择熔炼选项"""
        self.selected_option = option
        self.smelt_count = 1
        self.max_smelt_count = option["available_count"] // option["required_count"]
        self._update_count_display()
        self._update_count_buttons()
        self.smelt_btn.config(state="normal")
        self._update_selected_states(option)
        self._show_option_info(option)

    def _update_selected_states(self, selected_option: Dict[str, Any]):
        """更新所有选项的选中状态"""
        # 遍历所有选项框架
        for widget in self.options_frame.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Canvas):
                        # 找到滚动区域内的框架
                        scrollable_frame = child.winfo_children()[0]
                        for option_frame in scrollable_frame.winfo_children():
                            if hasattr(option_frame, 'option_data'):
                                # 检查是否是选中的选项
                                is_selected = (
                                    option_frame.option_data["current_rarity"] == selected_option["current_rarity"] and
                                    option_frame.option_data["type"] == selected_option["type"] and
                                    option_frame.option_data["is_random"] == selected_option["is_random"]
                                )

                                # 更新边框颜色
                                if is_selected:
                                    option_frame.config(
                                        highlightbackground=COLORS["highlight"],
                                        highlightthickness=3
                                    )
                                else:
                                    option_frame.config(
                                        highlightbackground=COLORS["border_light"],
                                        highlightthickness=2
                                    )

    def _show_default_info(self):
        """显示默认信息"""
        self._clear_info_frame()

        default_label = tk.Label(
            self.info_frame,
            text="请选择一个熔炼选项查看详细信息",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text_muted"],
            bg=COLORS["panel_bg"]
        )
        default_label.pack(expand=True)

    def _show_option_info(self, option: Dict[str, Any]):
        """显示选项详细信息"""
        self._clear_info_frame()

        # 创建滚动区域
        canvas = tk.Canvas(
            self.info_frame,
            bg=COLORS["panel_bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.info_frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        info_content = tk.Frame(canvas, bg=COLORS["panel_bg"])

        info_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=info_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        current_rarity = option["current_rarity"]
        next_rarity = option["next_rarity"]
        eq_type = option["type"]
        is_random = option["is_random"]
        required_count = option["required_count"]

        # 获取颜色
        current_color = RARITY_COLORS.get(current_rarity, COLORS["text"])
        next_color = RARITY_COLORS.get(next_rarity, COLORS["text"])

        # 标题
        title_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        title_label = tk.Label(
            title_frame,
            text="熔炼详情",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        title_label.pack(anchor=tk.W)

        # 稀有度转换
        rarity_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        rarity_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        current_rarity_label = tk.Label(
            rarity_frame,
            text=current_rarity.upper(),
            font=("Microsoft YaHei", 14, "bold"),
            fg=current_color,
            bg=COLORS["panel_bg"]
        )
        current_rarity_label.pack(side=tk.LEFT)

        arrow_label = tk.Label(
            rarity_frame,
            text="   →   ",
            font=("Microsoft YaHei", 14),
            fg=COLORS["text_secondary"],
            bg=COLORS["panel_bg"]
        )
        arrow_label.pack(side=tk.LEFT)

        next_rarity_label = tk.Label(
            rarity_frame,
            text=next_rarity.upper(),
            font=("Microsoft YaHei", 14, "bold"),
            fg=next_color,
            bg=COLORS["panel_bg"]
        )
        next_rarity_label.pack(side=tk.LEFT)

        # 类型信息
        type_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        type_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        if is_random:
            type_text = "随机装备类型 (八折优惠)"
            type_color = COLORS["highlight"]
        else:
            type_display = ITEM_TYPES.get(eq_type, eq_type)
            type_text = f"装备类型: {type_display}"
            type_color = COLORS["text"]

        type_label = tk.Label(
            type_frame,
            text=type_text,
            font=("Microsoft YaHei", 12),
            fg=type_color,
            bg=COLORS["panel_bg"]
        )
        type_label.pack(anchor=tk.W)

        # 所需材料
        materials_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        materials_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        materials_label = tk.Label(
            materials_frame,
            text="所需材料:",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        materials_label.pack(anchor=tk.W)

        materials_text = f"{required_count}件 {current_rarity}级装备"
        if not is_random:
            type_display = ITEM_TYPES.get(eq_type, eq_type)
            materials_text += f" ({type_display})"

        materials_detail = tk.Label(
            materials_frame,
            text=materials_text,
            font=("Microsoft YaHei", 11),
            fg=COLORS["warning"],
            bg=COLORS["panel_bg"]
        )
        materials_detail.pack(anchor=tk.W, pady=(2, 0))

        # 获取可用数量（从预计算缓存中，不需要遍历背包）
        available_count = option.get("available_count", 0)

        available_text = f"当前可用: {available_count}件"
        available_color = COLORS["success"] if available_count >= required_count else COLORS["danger"]

        available_label = tk.Label(
            materials_frame,
            text=available_text,
            font=("Microsoft YaHei", 11),
            fg=available_color,
            bg=COLORS["panel_bg"]
        )
        available_label.pack(anchor=tk.W, pady=(2, 0))

        # 最大可熔炼次数
        max_smelt = available_count // required_count
        max_smelt_label = tk.Label(
            materials_frame,
            text=f"最多可熔炼: {max_smelt} 次",
            font=("Microsoft YaHei", 11),
            fg=COLORS["highlight"],
            bg=COLORS["panel_bg"]
        )
        max_smelt_label.pack(anchor=tk.W, pady=(2, 0))

        # 可能的结果
        results_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        results_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        results_label = tk.Label(
            results_frame,
            text="可能获得:",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        results_label.pack(anchor=tk.W)

        results_text = f"1件随机{next_rarity}级装备"
        if not is_random:
            type_display = ITEM_TYPES.get(eq_type, eq_type)
            results_text += f" ({type_display})"

        results_detail = tk.Label(
            results_frame,
            text=results_text,
            font=("Microsoft YaHei", 11),
            fg=next_color,
            bg=COLORS["panel_bg"]
        )
        results_detail.pack(anchor=tk.W, pady=(2, 0))

        # 放置滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_count_display(self):
        """更新次数显示和按钮文字"""
        self.count_label.config(text=str(self.smelt_count))
        if self.selected_option:
            total_cost = self.smelt_count * self.selected_option["required_count"]
            self.smelt_btn.config(text=f"熔炼 ×{self.smelt_count}（消耗{total_cost}件）")

    def _update_count_buttons(self):
        """更新次数加减按钮状态"""
        self.count_minus_btn.config(state="normal" if self.smelt_count > 1 else "disabled")
        self.count_plus_btn.config(state="normal" if self.smelt_count < self.max_smelt_count else "disabled")
        self.count_max_btn.config(state="normal")
        self.smelt_btn.config(state="normal")

    def _decrease_count(self):
        """减少熔炼次数"""
        if self.smelt_count > 1:
            self.smelt_count -= 1
            self._update_count_display()
            self._update_count_buttons()

    def _increase_count(self):
        """增加熔炼次数"""
        if self.smelt_count < self.max_smelt_count:
            self.smelt_count += 1
            self._update_count_display()
            self._update_count_buttons()

    def _set_max_count(self):
        """设为最大熔炼次数"""
        self.smelt_count = self.max_smelt_count
        self._update_count_display()
        self._update_count_buttons()

    def _clear_info_frame(self):
        """清空信息区域"""
        for widget in self.info_frame.winfo_children():
            widget.destroy()

    def _smelt_items(self):
        """执行熔炼"""
        if not self.selected_option:
            show_toast("请先选择一个熔炼选项", self, toast_type="warning")
            return

        option = self.selected_option
        current_rarity = option["current_rarity"]
        eq_type = option["type"]
        is_random = option["is_random"]
        count = self.smelt_count

        # 确认对话框
        target_type = None if is_random else eq_type
        required_per_time = option["required_count"]
        total_required = required_per_time * count

        if count > 1:
            confirm_msg = f"确定要熔炼 {count} 次吗？\n\n"
            confirm_msg += f"消耗: {total_required}件 {current_rarity}级装备"
            if not is_random:
                type_display = ITEM_TYPES.get(eq_type, eq_type)
                confirm_msg += f" ({type_display})"
            confirm_msg += f"\n预计获得: {count}件随机{option['next_rarity']}级装备"
        else:
            confirm_msg = f"确定要熔炼{total_required}件{current_rarity}级装备吗？\n"
            if not is_random:
                type_display = ITEM_TYPES.get(eq_type, eq_type)
                confirm_msg += f"装备类型: {type_display}\n"
            else:
                confirm_msg += "装备类型: 随机 (八折优惠)\n"
            confirm_msg += f"将获得1件随机{option['next_rarity']}级装备"

        if not messagebox.askyesno("确认熔炼", confirm_msg):
            return

        # 执行熔炼
        success, message, results = self.smelting_manager.smelt_multiple(
            current_rarity, target_type, is_random, count
        )

        if success and results:
            show_toast(message, self, toast_type="success")

            # 刷新界面
            self._refresh_options()
            self.selected_option = None
            self.smelt_count = 1
            self._update_count_display()
            self.count_minus_btn.config(state="disabled")
            self.count_plus_btn.config(state="disabled")
            self.count_max_btn.config(state="disabled")
            self.smelt_btn.config(state="disabled")
            self._show_default_info()
        else:
            show_toast(message, self, toast_type="error")

    def refresh_all(self):
        """刷新所有显示"""
        self._refresh_options()
        self.selected_option = None
        self.smelt_count = 1
        self._update_count_display()
        self.count_minus_btn.config(state="disabled")
        self.count_plus_btn.config(state="disabled")
        self.count_max_btn.config(state="disabled")
        self.smelt_btn.config(state="disabled")
        self._show_default_info()