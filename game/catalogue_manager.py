"""
装备图鉴管理器
优化图鉴显示和管理的模块
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from game.constants import COLORS, RARITY_COLORS
from game.wheel_utils import bind_mouse_wheel_to_canvas
from game.attribute_utils import get_attribute_utils


class SortBy(Enum):
    """排序方式"""
    RARITY = "rarity"  # 按稀有度（参照背包的排序方式）


class FilterType(Enum):
    """筛选类型"""
    ALL = "all"        # 全部
    WEAPON = "weapon"  # 武器
    ARMOR = "armor"    # 护甲
    ACCESSORY = "accessory"  # 饰品


@dataclass
class CatalogueItem:
    """图鉴物品数据类"""
    item_id: str
    name: str
    rarity: str
    item_type: str
    description: str
    attributes: Dict[str, float]
    data: Dict[str, Any]  # 原始数据


class CatalogueManager:
    """图鉴管理器"""

    def __init__(self, gacha_manager):
        """初始化图鉴管理器"""
        self.gacha_manager = gacha_manager
        self.all_items: List[CatalogueItem] = []
        self.filtered_items: List[CatalogueItem] = []

        # 当前状态
        self.current_filter = FilterType.ALL
        self.current_sort = SortBy.RARITY
        self.search_text = ""

        # 稀有度排序顺序
        self.rarity_order = ["mythical", "legendary", "epic", "rare", "uncommon", "fine", "common"]

        # 类型显示名称
        self.type_names = {
            "weapon": "武器",
            "armor": "护甲",
            "accessory": "饰品"
        }

        # 初始化数据
        self._load_items()

    def _load_items(self):
        """加载所有物品数据"""
        self.all_items = []
        all_items_data = self.gacha_manager.all_items

        for item_id, item_data in all_items_data.items():
            item = CatalogueItem(
                item_id=item_id,
                name=item_data.get("name", "未知物品"),
                rarity=item_data.get("rarity", "common"),
                item_type=item_data.get("type", "unknown"),
                description=item_data.get("description", ""),
                attributes=item_data.get("attributes", {}),
                data=item_data
            )
            self.all_items.append(item)

        # 初始过滤和排序
        self._apply_filters()

    def set_filter(self, filter_type: FilterType):
        """设置筛选类型"""
        self.current_filter = filter_type
        self._apply_filters()

    def set_sort(self, sort_by: SortBy):
        """设置排序方式"""
        self.current_sort = sort_by
        self._apply_filters()

    def set_search(self, search_text: str):
        """设置搜索文本"""
        # 去除首尾空白字符
        self.search_text = search_text.strip().lower()
        self._apply_filters()

    def _apply_filters(self):
        """应用所有筛选和排序"""
        # 第一步：按类型筛选
        if self.current_filter == FilterType.ALL:
            filtered = self.all_items
        else:
            filtered = [item for item in self.all_items
                       if item.item_type == self.current_filter.value]

        # 第二步：按搜索文本筛选
        if self.search_text:
            # 将搜索文本和物品名称/描述都转换为小写进行比较
            # 对于中文字符，lower()不会改变字符，但可以处理混合文本
            search_text_lower = self.search_text.lower()

            # 在已经类型筛选的结果上进行搜索筛选
            search_filtered = []
            for item in filtered:
                # 确保名称和描述是字符串
                name = str(item.name) if item.name else ""
                description = str(item.description) if item.description else ""

                # 转换为小写进行比较
                name_lower = name.lower()
                description_lower = description.lower()

                # 检查是否包含搜索文本
                if (search_text_lower in name_lower or
                    search_text_lower in description_lower):
                    search_filtered.append(item)

            filtered = search_filtered

        # 第三步：排序（参照背包的排序方式）
        # 先按稀有度排序，稀有度相同按拼音排序
        from game.utils import get_pinyin_for_sort
        rarity_order = {"mythical": 0, "legendary": 1, "epic": 2, "rare": 3,
                       "uncommon": 4, "fine": 5, "common": 6}
        filtered.sort(key=lambda x: (
            rarity_order.get(x.rarity, 6),  # 稀有度排序
            get_pinyin_for_sort(x.name)     # 拼音排序
        ))

        self.filtered_items = filtered

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_items = len(self.filtered_items)

        # 稀有度统计
        rarity_counts = {}
        rarity_percentages = {}

        for rarity in self.rarity_order:
            count = len([item for item in self.filtered_items if item.rarity == rarity])
            rarity_counts[rarity] = count
            rarity_percentages[rarity] = round((count / total_items * 100), 2) if total_items > 0 else 0

        # 类型统计
        type_counts = {}
        type_percentages = {}

        for item_type in ["weapon", "armor", "accessory"]:
            count = len([item for item in self.filtered_items if item.item_type == item_type])
            type_counts[item_type] = count
            type_percentages[item_type] = round((count / total_items * 100), 2) if total_items > 0 else 0

        return {
            "total_items": total_items,
            "rarity_counts": rarity_counts,
            "rarity_percentages": rarity_percentages,
            "type_counts": type_counts,
            "type_percentages": type_percentages,
            "filtered_items": self.filtered_items
        }

    def get_type_statistics(self, pool_type: str) -> Dict[str, Any]:
        """获取指定类型的统计信息"""
        if pool_type == "all":
            return self.get_statistics()

        # 筛选指定类型的物品
        type_items = [item for item in self.all_items if item.item_type == pool_type]
        total_items = len(type_items)

        # 稀有度统计
        rarity_counts = {}
        rarity_percentages = {}

        for rarity in self.rarity_order:
            count = len([item for item in type_items if item.rarity == rarity])
            rarity_counts[rarity] = count
            rarity_percentages[rarity] = round((count / total_items * 100), 2) if total_items > 0 else 0

        return {
            "total_items": total_items,
            "rarity_counts": rarity_counts,
            "rarity_percentages": rarity_percentages,
            "type_name": self.type_names.get(pool_type, pool_type)
        }


class CatalogueUI:
    """图鉴UI组件"""

    def __init__(self, parent, catalogue_manager: CatalogueManager):
        """初始化图鉴UI"""
        self.parent = parent
        self.catalogue_manager = catalogue_manager

        # 创建主框架
        self.main_frame = tk.Frame(parent, bg=COLORS["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 控制面板
        self._create_control_panel()

        # 内容区域
        self._create_content_area()

        # 初始显示
        self.refresh()

    def _create_control_panel(self):
        """创建控制面板"""
        control_frame = tk.Frame(self.main_frame, bg=COLORS["panel_bg"],
                                highlightbackground=COLORS["border"],
                                highlightthickness=1,
                                relief="solid",
                                padx=15, pady=15)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 15))

        # 标题
        title_label = tk.Label(
            control_frame,
            text="装备图鉴",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))

        # 搜索框
        search_frame = tk.Frame(control_frame, bg=COLORS["panel_bg"])
        search_frame.pack(fill=tk.X, pady=(0, 10))

        search_label = tk.Label(
            search_frame,
            text="搜索:",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        search_label.pack(side=tk.LEFT, padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei", 11),
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="solid",
            borderwidth=1
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 筛选和排序按钮
        filter_sort_frame = tk.Frame(control_frame, bg=COLORS["panel_bg"])
        filter_sort_frame.pack(fill=tk.X)

        # 筛选按钮
        filter_label = tk.Label(
            filter_sort_frame,
            text="筛选:",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        filter_label.pack(side=tk.LEFT, padx=(0, 10))

        self.filter_buttons = {}
        for filter_type in FilterType:
            btn = tk.Button(
                filter_sort_frame,
                text=self._get_filter_display_name(filter_type),
                font=("Microsoft YaHei", 10),
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["button_hover"],
                activeforeground=COLORS["text"],
                relief="flat",
                cursor="hand2",
                command=lambda ft=filter_type: self._on_filter_changed(ft)
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.filter_buttons[filter_type] = btn

        # 排序信息（只显示当前排序方式，没有按钮）
        sort_info = tk.Label(
            filter_sort_frame,
            text="排序: 稀有度（神话→普通）",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        sort_info.pack(side=tk.LEFT, padx=(20, 10))

        # 不再需要排序按钮，因为只有一种排序方式
        self.sort_buttons = {}

        # 初始选中状态
        self._update_button_states()

    def _create_content_area(self):
        """创建内容区域"""
        # 创建滚动区域
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=COLORS["background"],
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            self.main_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )

        self.content_frame = tk.Frame(self.canvas, bg=COLORS["background"])

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_canvas(self.canvas, self.content_frame)

        # 放置滚动组件
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _get_filter_display_name(self, filter_type: FilterType) -> str:
        """获取筛选类型的显示名称"""
        names = {
            FilterType.ALL: "全部",
            FilterType.WEAPON: "武器",
            FilterType.ARMOR: "护甲",
            FilterType.ACCESSORY: "饰品"
        }
        return names.get(filter_type, filter_type.value)

    def _get_sort_display_name(self, sort_by: SortBy) -> str:
        """获取排序方式的显示名称（现在只有稀有度排序）"""
        return "稀有度"

    def _on_search_changed(self, *args):
        """搜索文本变化回调"""
        search_text = self.search_var.get()
        # 去除首尾空白字符
        search_text = search_text.strip()
        self.catalogue_manager.set_search(search_text)
        self.refresh()

    def _on_filter_changed(self, filter_type: FilterType):
        """筛选类型变化回调"""
        self.catalogue_manager.set_filter(filter_type)
        self._update_button_states()
        self.refresh()

    def _on_sort_changed(self, sort_by: SortBy):
        """排序方式变化回调（现在只有一种排序方式，所以不需要处理）"""
        pass

    def _update_button_states(self):
        """更新按钮状态"""
        # 更新筛选按钮
        for filter_type, button in self.filter_buttons.items():
            if filter_type == self.catalogue_manager.current_filter:
                button.config(bg=COLORS["success"])
            else:
                button.config(bg=COLORS["button"])

        # 不再需要更新排序按钮，因为只有一种排序方式

    def refresh(self):
        """刷新显示"""
        # 清空内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 获取统计信息
        stats = self.catalogue_manager.get_statistics()

        # 显示统计信息
        self._display_statistics(stats)

        # 显示物品列表
        self._display_items(stats["filtered_items"])

    def _display_statistics(self, stats: Dict[str, Any]):
        """显示统计信息"""
        stats_frame = tk.Frame(self.content_frame, bg=COLORS["panel_bg"],
                              highlightbackground=COLORS["border"],
                              highlightthickness=1,
                              relief="solid",
                              padx=15, pady=15)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        # 统计标题
        filter_name = self._get_filter_display_name(self.catalogue_manager.current_filter)
        stats_title = tk.Label(
            stats_frame,
            text=f"{filter_name} 统计 ({stats['total_items']}件)",
            font=("Microsoft YaHei", 14, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        stats_title.pack(anchor=tk.W, pady=(0, 10))

        # 类型分布
        if self.catalogue_manager.current_filter == FilterType.ALL:
            type_frame = tk.Frame(stats_frame, bg=COLORS["panel_bg"])
            type_frame.pack(fill=tk.X, pady=(0, 10))

            type_label = tk.Label(
                type_frame,
                text="类型分布:",
                font=("Microsoft YaHei", 12, "bold"),
                fg=COLORS["text"],
                bg=COLORS["panel_bg"]
            )
            type_label.pack(anchor=tk.W, pady=(0, 5))

            for item_type, count in stats["type_counts"].items():
                if count > 0:
                    percentage = stats["type_percentages"][item_type]
                    type_name = self.catalogue_manager.type_names.get(item_type, item_type)

                    type_item = tk.Label(
                        type_frame,
                        text=f"{type_name}: {count}件 ({percentage}%)",
                        font=("Microsoft YaHei", 11),
                        fg=COLORS["text_secondary"],
                        bg=COLORS["panel_bg"]
                    )
                    type_item.pack(anchor=tk.W, pady=(0, 3))

        # 稀有度分布
        rarity_frame = tk.Frame(stats_frame, bg=COLORS["panel_bg"])
        rarity_frame.pack(fill=tk.X)

        rarity_label = tk.Label(
            rarity_frame,
            text="稀有度分布:",
            font=("Microsoft YaHei", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel_bg"]
        )
        rarity_label.pack(anchor=tk.W, pady=(0, 5))

        for rarity, count in stats["rarity_counts"].items():
            if count > 0:
                percentage = stats["rarity_percentages"][rarity]
                rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])

                rarity_item = tk.Label(
                    rarity_frame,
                    text=f"{rarity}: {count}件 ({percentage}%)",
                    font=("Microsoft YaHei", 11),
                    fg=rarity_color,
                    bg=COLORS["panel_bg"]
                )
                rarity_item.pack(anchor=tk.W, pady=(0, 3))

    def _display_items(self, items: List[CatalogueItem]):
        """显示物品列表"""
        if not items:
            # 显示空状态
            empty_frame = tk.Frame(self.content_frame, bg=COLORS["panel_bg"],
                                  highlightbackground=COLORS["border"],
                                  highlightthickness=1,
                                  relief="solid",
                                  padx=15, pady=15)
            empty_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

            empty_label = tk.Label(
                empty_frame,
                text="暂无符合条件的装备",
                font=("Microsoft YaHei", 14),
                fg=COLORS["text_muted"],
                bg=COLORS["panel_bg"]
            )
            empty_label.pack(expand=True)
            return

        # 直接显示所有物品
        for item in items:
            self._create_item_display(item)


    def _create_item_display(self, item: CatalogueItem, parent=None):
        """创建物品显示"""
        if parent is None:
            parent = self.content_frame

        item_frame = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            relief="solid",
            padx=10,
            pady=8
        )
        item_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        rarity_color = RARITY_COLORS.get(item.rarity, COLORS["text"])

        # 名称和稀有度
        header_frame = tk.Frame(item_frame, bg=COLORS["card_bg"])
        header_frame.pack(fill=tk.X, pady=(0, 5))

        name_label = tk.Label(
            header_frame,
            text=item.name,
            font=("Microsoft YaHei", 12, "bold"),
            fg=rarity_color,
            bg=COLORS["card_bg"]
        )
        name_label.pack(side=tk.LEFT)

        rarity_label = tk.Label(
            header_frame,
            text=f"[{item.rarity}]",
            font=("Microsoft YaHei", 10),
            fg=rarity_color,
            bg=COLORS["card_bg"]
        )
        rarity_label.pack(side=tk.LEFT, padx=(10, 0))

        type_label = tk.Label(
            header_frame,
            text=f"类型: {self.catalogue_manager.type_names.get(item.item_type, item.item_type)}",
            font=("Microsoft YaHei", 10),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        type_label.pack(side=tk.RIGHT)

        # 描述
        if item.description:
            desc_label = tk.Label(
                item_frame,
                text=item.description,
                font=("Microsoft YaHei", 9),
                fg=COLORS["text"],
                bg=COLORS["card_bg"],
                wraplength=500,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, pady=(0, 5))

        # 属性
        if item.attributes:
            attrs_frame = tk.Frame(item_frame, bg=COLORS["card_bg"])
            attrs_frame.pack(anchor=tk.W)

            for attr_name, attr_value in item.attributes.items():
                display_name = self._get_attribute_display_name(attr_name)
                value_str = self._format_attribute_value(attr_name, attr_value)

                attr_label = tk.Label(
                    attrs_frame,
                    text=f"{display_name}: {value_str}",
                    font=("Microsoft YaHei", 9),
                    fg=COLORS["info"],
                    bg=COLORS["card_bg"]
                )
                attr_label.pack(side=tk.LEFT, padx=(0, 10))

    def _get_attribute_display_name(self, attr_name: str) -> str:
        """获取属性显示名称"""
        attribute_utils = get_attribute_utils()
        return attribute_utils.get_attribute_display_name(attr_name)

    def _format_attribute_value(self, attr_name: str, attr_value: float) -> str:
        """格式化属性值"""
        attribute_utils = get_attribute_utils()
        return attribute_utils.format_attribute(attr_name, attr_value)