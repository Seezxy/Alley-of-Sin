"""
抽奖界面模块（Frame版本）
负责抽奖界面的显示和交互，作为Frame嵌入主窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any

from game.constants import (
    COLORS, GACHA_PRICE, GACHA_TEN_PRICE, GACHA_HUNDRED_PRICE, GACHA_POOLS, GACHA_TYPES,
    GACHA_PROBABILITIES, RARITY_COLORS
)
from game.gacha_manager import get_gacha_manager
from game.user_manager import get_user_manager
from game.catalogue_manager import CatalogueManager, CatalogueUI
from game.wheel_utils import bind_mouse_wheel_to_canvas
from game.toast import show_toast




class GachaFrame(tk.Frame):
    """抽奖界面（Frame版本）"""

    def __init__(self, parent, on_back):
        super().__init__(parent, bg=COLORS["background"])
        self.on_back = on_back  # 返回回调函数

        # 获取管理器实例
        self.gacha_manager = get_gacha_manager()
        self.user_manager = get_user_manager()

        # 初始化图鉴管理器
        self.catalogue_manager = CatalogueManager(self.gacha_manager)

        # 当前选择的抽奖池（抽奖用）和图鉴模式
        self.current_pool = "weapon"
        self.catalogue_mode = "all"  # 图鉴模式：all显示全部装备，pool显示当前池装备

        # 界面组件
        self.result_frame = None
        self.catalogue_frame = None
        self.catalogue_ui = None  # 新的图鉴UI组件
        self._catalogue_loaded = False  # 图鉴懒加载标记
        self._notebook = None  # 选项卡组件引用

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
            text="🎰 抽 奖 系 统 🎰",
            font=("Microsoft YaHei", 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        title_label.pack(side=tk.LEFT, padx=(20, 0))

        # 货币显示（右侧）
        currency_frame = tk.Frame(header_frame, bg=COLORS["background"])
        currency_frame.pack(side=tk.RIGHT)

        # 获取货币数量
        currency_amount = self.user_manager.get_currency()

        self.currency_label = tk.Label(
            currency_frame,
            text=f"💵 {currency_amount}",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["highlight"],
            bg=COLORS["background"]
        )
        self.currency_label.pack()

        # 内容区域（左右布局）
        content_frame = tk.Frame(main_container, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：抽奖控制区域
        left_frame = tk.Frame(content_frame, bg=COLORS["background"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 抽奖池选择
        pool_frame = tk.Frame(left_frame, bg=COLORS["panel_bg"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1,
                             relief="solid",
                             padx=15, pady=15)
        pool_frame.pack(fill=tk.X, pady=(0, 15))

        pool_label = tk.Label(
            pool_frame,
            text="选择抽奖池:",
            font=("Microsoft YaHei", 14, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        pool_label.pack(anchor=tk.W, pady=(0, 10))

        # 抽奖池按钮
        pool_buttons_frame = tk.Frame(pool_frame, bg=COLORS["panel_bg"])
        pool_buttons_frame.pack(fill=tk.X)

        self.pool_buttons = {}
        for pool_key, pool_name in GACHA_POOLS.items():
            # "全部"池只用于图鉴，不能抽奖
            is_all_pool = (pool_key == "all")
            pool_btn = tk.Button(
                pool_buttons_frame,
                text=pool_name,
                font=("Microsoft YaHei", 12),
                bg=COLORS["button"] if pool_key != self.current_pool else COLORS["success"],
                fg=COLORS["text"],
                activebackground=COLORS["button_hover"],
                activeforeground=COLORS["text"],
                relief="flat",
                cursor="hand2" if not is_all_pool else "arrow",
                command=lambda p=pool_key: self._select_pool(p)
            )
            pool_btn.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
            self.pool_buttons[pool_key] = pool_btn

        # 抽奖操作区域
        action_frame = tk.Frame(left_frame, bg=COLORS["panel_bg"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1,
                               relief="solid",
                               padx=15, pady=15)
        action_frame.pack(fill=tk.BOTH, expand=True)

        action_label = tk.Label(
            action_frame,
            text="抽奖操作:",
            font=("Microsoft YaHei", 14, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        action_label.pack(anchor=tk.W, pady=(0, 15))

        # 单抽按钮
        self.single_btn = tk.Button(
            action_frame,
            text=f"单抽 ({GACHA_PRICE}钞票)",
            font=("Microsoft YaHei", 13),
            bg=COLORS["info"],
            fg=COLORS["text"],
            activebackground=COLORS["info_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            height=2,
            command=lambda: self._perform_draw("single")
        )
        self.single_btn.pack(fill=tk.X, pady=(0, 10))

        # 十连抽按钮
        self.ten_btn = tk.Button(
            action_frame,
            text=f"十连抽 ({GACHA_TEN_PRICE}钞票)",
            font=("Microsoft YaHei", 13),
            bg=COLORS["warning"],
            fg=COLORS["text"],
            activebackground=COLORS["warning_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            height=2,
            command=lambda: self._perform_draw("ten")
        )
        self.ten_btn.pack(fill=tk.X, pady=(0, 10))

        # 百连抽按钮
        self.hundred_btn = tk.Button(
            action_frame,
            text=f"百连抽 ({GACHA_HUNDRED_PRICE}钞票)",
            font=("Microsoft YaHei", 13),
            bg=COLORS["success"],
            fg=COLORS["text"],
            activebackground=COLORS["success_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            height=2,
            command=lambda: self._perform_draw("hundred")
        )
        self.hundred_btn.pack(fill=tk.X, pady=(0, 10))

        # 尽数抽按钮
        max_draws = self.gacha_manager.get_max_draws()
        max_cost = max_draws * GACHA_PRICE if max_draws > 0 else 0
        max_text = f"尽数抽 ({max_draws}抽, {max_cost}钞票)" if max_draws > 0 else "货币不足"

        self.max_btn = tk.Button(
            action_frame,
            text=max_text,
            font=("Microsoft YaHei", 13),
            bg=COLORS["danger"] if max_draws > 0 else COLORS["button_disabled"],
            fg=COLORS["text"],
            activebackground=COLORS["danger_light"] if max_draws > 0 else COLORS["button_disabled"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2" if max_draws > 0 else "arrow",
            height=2,
            state=tk.NORMAL if max_draws > 0 else tk.DISABLED,
            command=lambda: self._perform_draw("max")
        )
        self.max_btn.pack(fill=tk.X)

        # 概率显示
        prob_frame = tk.Frame(action_frame, bg=COLORS["panel_bg"])
        prob_frame.pack(fill=tk.X, pady=(20, 0))

        prob_label = tk.Label(
            prob_frame,
            text="抽奖概率:",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        prob_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        rarity_names = {
            "common": "普通", "fine": "精品", "uncommon": "优秀",
            "rare": "罕见", "epic": "史诗", "legendary": "传说", "mythical": "神话",
        }
        # 左列4个，右列3个
        items = list(GACHA_PROBABILITIES.items())
        for i, (rarity, prob) in enumerate(items):
            col = 0 if i < 4 else 1
            row = i + 1 if i < 4 else i - 3  # +1 因为第0行是标题
            rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])
            cn_name = rarity_names.get(rarity, rarity)
            prob_text = f"{cn_name}: {prob}%"

            prob_item = tk.Label(
                prob_frame,
                text=prob_text,
                font=("Microsoft YaHei", 11),
                fg=rarity_color,
                bg=COLORS["panel_bg"]
            )
            prob_item.grid(row=row, column=col, sticky=tk.W, padx=(0, 30), pady=2)

        # 右侧：结果和装备图鉴区域
        right_frame = tk.Frame(content_frame, bg=COLORS["background"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 选项卡
        self._notebook = ttk.Notebook(right_frame)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # 抽奖结果标签页
        self.result_frame = tk.Frame(self._notebook, bg=COLORS["background"])
        self._notebook.add(self.result_frame, text="抽奖结果")

        # 装备图鉴标签页（懒加载）
        self.catalogue_frame = tk.Frame(self._notebook, bg=COLORS["background"])
        self._notebook.add(self.catalogue_frame, text="装备图鉴")

        # 初始化标签页内容
        self._setup_result_tab()
        # 图鉴标签页延迟到用户切换时创建
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 初始化抽奖按钮状态
        self._refresh_draw_buttons()

    def _on_tab_changed(self, event):
        """选项卡切换回调，懒加载图鉴标签页"""
        if not self._catalogue_loaded:
            try:
                current_idx = self._notebook.index("current")
                if current_idx == 1:  # 装备图鉴是第2个标签页
                    self._setup_catalogue_tab()
                    self._catalogue_loaded = True
            except tk.TclError:
                pass

    def _select_pool(self, pool_key: str):
        """选择抽奖池"""
        self.current_pool = pool_key
        self._refresh_pool_buttons()
        self._refresh_draw_buttons()
        # 如果图鉴模式是pool，刷新图鉴
        if self.catalogue_mode == "pool":
            self._refresh_catalogue()

    def _refresh_pool_buttons(self):
        """刷新抽奖池按钮状态"""
        for pool_key, button in self.pool_buttons.items():
            if pool_key == self.current_pool:
                button.config(bg=COLORS["success"])
            else:
                button.config(bg=COLORS["button"])

    def _perform_draw(self, draw_type: str):
        """执行抽奖"""
        if draw_type == "single":
            success, item_data, message = self.gacha_manager.perform_single_draw(self.current_pool)
            items = [item_data] if item_data else []
        elif draw_type == "ten":
            success, items, message = self.gacha_manager.perform_ten_draw(self.current_pool)
        elif draw_type == "hundred":
            success, items, message = self.gacha_manager.perform_hundred_draw(self.current_pool)
        elif draw_type == "max":
            success, items, message = self.gacha_manager.perform_max_draw(self.current_pool)
        else:
            return

        if success:
            # 显示结果
            self._show_draw_results(items)
            # 刷新货币显示
            self._refresh_currency()
            # 刷新尽数抽按钮
            self._refresh_max_button()
            # 显示成功消息
            show_toast(message, self, toast_type="success")
        else:
            show_toast(message, self, toast_type="error")

    def _show_draw_results(self, items: List[Dict[str, Any]]):
        """显示抽奖结果"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if not items:
            empty_label = tk.Label(
                self.result_frame,
                text="暂无抽奖结果",
                font=("Microsoft YaHei", 14),
                fg=COLORS["text_muted"],
                bg=COLORS["background"]
            )
            empty_label.pack(expand=True)
            return

        # 大量物品时只显示统计摘要，避免创建大量 widget 导致闪退
        if len(items) > 30:
            self._show_draw_summary(items)
            return

        # 少量物品：逐件显示
        self._show_draw_items(items)

    def _show_draw_summary(self, items: List[Dict[str, Any]]):
        """显示大量抽奖结果的统计摘要"""
        from collections import Counter

        # 统计稀有度分布
        rarity_counts = Counter(item.get("rarity", "common") for item in items)
        type_counts = Counter(item.get("type", "unknown") for item in items)

        content = tk.Frame(self.result_frame, bg=COLORS["background"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            content,
            text=f"抽奖结果 ({len(items)} 件物品)",
            font=("Microsoft YaHei", 18, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))

        # 稀有度分布
        rarity_frame = tk.Frame(content, bg=COLORS["panel_bg"],
                               highlightbackground=COLORS["border"],
                               highlightthickness=1, relief="solid",
                               padx=15, pady=15)
        rarity_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(rarity_frame, text="稀有度分布:", font=("Microsoft YaHei", 13, "bold"),
                fg=COLORS["text"], bg=COLORS["panel_bg"]).pack(anchor=tk.W, pady=(0, 8))

        rarity_order = ["mythical", "legendary", "epic", "rare", "uncommon", "fine", "common"]
        for rarity in rarity_order:
            count = rarity_counts.get(rarity, 0)
            if count > 0:
                pct = count / len(items) * 100
                color = RARITY_COLORS.get(rarity, COLORS["text"])
                tk.Label(rarity_frame,
                        text=f"  {rarity}: {count} 件 ({pct:.1f}%)",
                        font=("Microsoft YaHei", 12),
                        fg=color, bg=COLORS["panel_bg"]).pack(anchor=tk.W, pady=(0, 2))

        # 类型分布
        type_frame = tk.Frame(content, bg=COLORS["panel_bg"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1, relief="solid",
                             padx=15, pady=15)
        type_frame.pack(fill=tk.X, pady=(0, 10))

        type_names = {"weapon": "武器", "armor": "护甲", "accessory": "饰品"}
        tk.Label(type_frame, text="类型分布:", font=("Microsoft YaHei", 13, "bold"),
                fg=COLORS["text"], bg=COLORS["panel_bg"]).pack(anchor=tk.W, pady=(0, 8))

        for itype, name in type_names.items():
            count = type_counts.get(itype, 0)
            if count > 0:
                pct = count / len(items) * 100
                tk.Label(type_frame,
                        text=f"  {name}: {count} 件 ({pct:.1f}%)",
                        font=("Microsoft YaHei", 12),
                        fg=COLORS["text_secondary"], bg=COLORS["panel_bg"]).pack(anchor=tk.W, pady=(0, 2))

        # 提示
        tk.Label(content,
                text="详细信息请查看背包",
                font=("Microsoft YaHei", 11),
                fg=COLORS["text_muted"],
                bg=COLORS["background"]).pack(pady=(15, 0))

    def _show_draw_items(self, items: List[Dict[str, Any]]):
        """显示少量抽奖结果（逐件显示）"""
        canvas = tk.Canvas(
            self.result_frame,
            bg=COLORS["background"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.result_frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        results_content = tk.Frame(canvas, bg=COLORS["background"])

        canvas.create_window((0, 0), window=results_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        bind_mouse_wheel_to_canvas(canvas, results_content)

        title_label = tk.Label(
            results_content,
            text=f"本次抽奖结果 ({len(items)} 个物品):",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        title_label.pack(anchor=tk.W, padx=10, pady=(10, 15))

        for i, item_data in enumerate(items):
            item_frame = self._create_result_item_display(results_content, item_data, i+1)
            item_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 所有物品创建完毕后绑定Configure和更新scrollregion
        results_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_result_item_display(self, parent, item_data: Dict[str, Any], index: int) -> tk.Frame:
        """创建抽奖结果物品显示"""
        name = item_data.get("name", "未知物品")
        rarity = item_data.get("rarity", "common")
        description = item_data.get("description", "")
        item_type = item_data.get("type", "unknown")

        rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])

        # 物品框架
        item_frame = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            relief="solid",
            padx=15,
            pady=10
        )

        # 序号和名称
        header_frame = tk.Frame(item_frame, bg=COLORS["card_bg"])
        header_frame.pack(fill=tk.X, pady=(0, 5))

        index_label = tk.Label(
            header_frame,
            text=f"{index}.",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        index_label.pack(side=tk.LEFT)

        name_label = tk.Label(
            header_frame,
            text=name,
            font=("Microsoft YaHei", 14, "bold"),
            fg=rarity_color,
            bg=COLORS["card_bg"]
        )
        name_label.pack(side=tk.LEFT, padx=(10, 0))

        rarity_label = tk.Label(
            header_frame,
            text=f"[{rarity}]",
            font=("Microsoft YaHei", 11),
            fg=rarity_color,
            bg=COLORS["card_bg"]
        )
        rarity_label.pack(side=tk.RIGHT)

        # 类型和描述
        type_label = tk.Label(
            item_frame,
            text=f"类型: {item_type}",
            font=("Microsoft YaHei", 11),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        type_label.pack(anchor=tk.W)

        if description:
            desc_label = tk.Label(
                item_frame,
                text=description,
                font=("Microsoft YaHei", 10),
                fg=COLORS["text"],
                bg=COLORS["card_bg"],
                wraplength=400,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, pady=(5, 0))

        return item_frame

    def _setup_result_tab(self):
        """设置抽奖结果标签页"""
        empty_label = tk.Label(
            self.result_frame,
            text="暂无抽奖记录\n点击左侧按钮开始抽奖",
            font=("Microsoft YaHei", 14),
            fg=COLORS["text_muted"],
            bg=COLORS["background"],
            justify=tk.CENTER
        )
        empty_label.pack(expand=True)

    def _setup_catalogue_tab(self):
        """设置装备图鉴标签页"""
        # 清空图鉴区域
        for widget in self.catalogue_frame.winfo_children():
            widget.destroy()

        # 创建新的图鉴UI
        self.catalogue_ui = CatalogueUI(self.catalogue_frame, self.catalogue_manager)

    def _refresh_catalogue(self):
        """刷新装备图鉴（兼容旧代码）"""
        if self.catalogue_ui:
            self.catalogue_ui.refresh()


    def _refresh_currency(self):
        """刷新货币显示"""
        if hasattr(self, 'currency_label'):
            currency_amount = self.user_manager.get_currency()
            self.currency_label.config(text=f"💵 {currency_amount}")

    def _refresh_max_button(self):
        """刷新尽数抽按钮"""
        if hasattr(self, 'max_btn'):
            max_draws = self.gacha_manager.get_max_draws()
            max_cost = max_draws * GACHA_PRICE if max_draws > 0 else 0
            max_text = f"尽数抽 ({max_draws}抽, {max_cost}钞票)" if max_draws > 0 else "货币不足"

            self.max_btn.config(
                text=max_text,
                bg=COLORS["danger"] if max_draws > 0 else COLORS["button_disabled"],
                activebackground=COLORS["danger_light"] if max_draws > 0 else COLORS["button_disabled"],
                cursor="hand2" if max_draws > 0 else "arrow",
                state=tk.NORMAL if max_draws > 0 else tk.DISABLED
            )

    def _refresh_draw_buttons(self):
        """刷新所有抽奖按钮"""
        # 刷新单抽、十连抽和百连抽按钮
        if hasattr(self, 'single_btn') and hasattr(self, 'ten_btn') and hasattr(self, 'hundred_btn'):
            # 启用所有抽奖按钮（包括"全部"池）
            self.single_btn.config(
                bg=COLORS["info"],
                activebackground=COLORS["info_light"],
                cursor="hand2",
                state=tk.NORMAL
            )
            self.ten_btn.config(
                bg=COLORS["warning"],
                activebackground=COLORS["warning_light"],
                cursor="hand2",
                state=tk.NORMAL
            )
            self.hundred_btn.config(
                bg=COLORS["success"],
                activebackground=COLORS["success_light"],
                cursor="hand2",
                state=tk.NORMAL
            )

        # 刷新尽数抽按钮
        if hasattr(self, 'max_btn'):
            max_draws = self.gacha_manager.get_max_draws()
            max_cost = max_draws * GACHA_PRICE if max_draws > 0 else 0
            max_text = f"尽数抽 ({max_draws}抽, {max_cost}钞票)" if max_draws > 0 else "货币不足"

            self.max_btn.config(
                text=max_text,
                bg=COLORS["danger"] if max_draws > 0 else COLORS["button_disabled"],
                activebackground=COLORS["danger_light"] if max_draws > 0 else COLORS["button_disabled"],
                cursor="hand2" if max_draws > 0 else "arrow",
                state=tk.NORMAL if max_draws > 0 else tk.DISABLED
            )

    def refresh_all(self):
        """刷新动态内容（货币、按钮状态等）"""
        self._refresh_currency()
        self._refresh_draw_buttons()