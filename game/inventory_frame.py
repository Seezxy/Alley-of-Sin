"""
背包界面模块（Frame版本）
负责背包界面的显示和交互，作为Frame嵌入主窗口
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any

from game.constants import (
    COLORS, INVENTORY_WINDOW_TITLE, INVENTORY_WINDOW_WIDTH, INVENTORY_WINDOW_HEIGHT,
    RARITY_COLORS, ITEM_TYPES, EQUIPMENT_SLOTS, ATTRIBUTE_DISPLAY_NAMES
)
from game.inventory import get_inventory_manager
from game.item_manager import get_item_manager
from game.user_manager import get_user_manager
from game.wheel_utils import bind_mouse_wheel_to_canvas
from game.toast import show_toast


class InventoryFrame(tk.Frame):
    """背包界面（Frame版本）"""

    ITEMS_PER_PAGE = 50

    def __init__(self, parent, on_back, on_smelting=None):
        super().__init__(parent, bg=COLORS["background"])
        self.on_back = on_back  # 返回回调函数
        self.on_smelting = on_smelting  # 熔炼回调函数

        # 获取管理器实例
        self.inventory_manager = get_inventory_manager()
        self.item_manager = get_item_manager()

        # 界面组件
        self.equipment_frame = None
        self.inventory_frame = None
        self.info_frame = None
        self.selected_item = None
        self.capacity_label = None  # 容量显示标签
        self.page_nav_frame = None  # 页码导航区域

        # 分类和排序状态
        self.current_filter = "all"  # 当前筛选类型：all, weapon, armor, accessory
        self.current_sort = "rarity"   # 当前排序方式：name, rarity（默认稀有度）
        self.current_search = None     # 当前搜索文本

        # 分页状态
        self.current_page = 0
        self.total_pages = 0
        self._all_filtered_items = []  # 缓存当前筛选结果

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
            text="背 包",
            font=("Microsoft YaHei", 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        title_label.pack(side=tk.LEFT, padx=(20, 0))

        # 熔炼按钮
        smelting_button = tk.Button(
            header_frame,
            text="🔥 熔炼",
            font=("Microsoft YaHei", 12, "bold"),
            bg=COLORS["warning"],
            fg=COLORS["text"],
            activebackground=COLORS["warning_light"],
            activeforeground=COLORS["text"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._open_smelting,
            padx=10,
            pady=2
        )
        smelting_button.pack(side=tk.LEFT, padx=(15, 0))

        # 货币显示（右侧）
        currency_frame = tk.Frame(header_frame, bg=COLORS["background"])
        currency_frame.pack(side=tk.RIGHT)

        # 获取货币数量
        user_manager = get_user_manager()
        currency_amount = user_manager.get_currency()

        currency_label = tk.Label(
            currency_frame,
            text=f"💵 {currency_amount}",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["highlight"],
            bg=COLORS["background"]
        )
        currency_label.pack()

        # 内容区域（左右布局）
        content_frame = tk.Frame(main_container, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：装备区域
        left_frame = tk.Frame(content_frame, bg=COLORS["background"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 装备标题
        equipment_label = tk.Label(
            left_frame,
            text="装 备",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        equipment_label.pack(anchor=tk.W, pady=(0, 10))

        # 装备面板
        self.equipment_frame = tk.Frame(
            left_frame,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid"
        )
        self.equipment_frame.pack(fill=tk.BOTH, expand=True)

        # 右侧：背包区域
        right_frame = tk.Frame(content_frame, bg=COLORS["background"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 背包标题和容量信息
        inventory_header = tk.Frame(right_frame, bg=COLORS["background"])
        inventory_header.pack(fill=tk.X, pady=(0, 5))

        # 标题和容量信息在同一行
        title_frame = tk.Frame(inventory_header, bg=COLORS["background"])
        title_frame.pack(fill=tk.X, pady=(0, 5))

        inventory_label = tk.Label(
            title_frame,
            text="背 包",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        inventory_label.pack(side=tk.LEFT, anchor=tk.W)

        # 容量信息
        capacity_info = self._get_capacity_info()
        self.capacity_label = tk.Label(
            title_frame,
            text=capacity_info,
            font=("Microsoft YaHei", 12),
            fg=COLORS["text_secondary"],
            bg=COLORS["background"]
        )
        self.capacity_label.pack(side=tk.RIGHT, anchor=tk.E)

        # 分类和排序控制面板
        control_panel = tk.Frame(inventory_header, bg=COLORS["background"])
        control_panel.pack(fill=tk.X, pady=(5, 0))

        # 分类筛选标签
        filter_label = tk.Label(
            control_panel,
            text="分类:",
            font=("Microsoft YaHei", 11, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        filter_label.pack(side=tk.LEFT, padx=(0, 10))

        # 分类按钮
        self.filter_buttons = {}
        filter_types = [
            ("all", "全部"),
            ("weapon", "武器"),
            ("armor", "护甲"),
            ("accessory", "饰品")
        ]

        for filter_key, filter_name in filter_types:
            btn = tk.Button(
                control_panel,
                text=filter_name,
                font=("Microsoft YaHei", 10),
                bg=COLORS["button"] if filter_key != self.current_filter else COLORS["success"],
                fg=COLORS["text"],
                activebackground=COLORS["button_hover"],
                activeforeground=COLORS["text"],
                relief="flat",
                cursor="hand2",
                command=lambda f=filter_key: self._apply_filter(f)
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.filter_buttons[filter_key] = btn

        # 分隔符
        separator = tk.Label(
            control_panel,
            text="|",
            font=("Microsoft YaHei", 11),
            fg=COLORS["text_muted"],
            bg=COLORS["background"]
        )
        separator.pack(side=tk.LEFT, padx=(15, 10))


        # 查找功能
        tk.Label(control_panel, text="查找:", font=("Microsoft YaHei", 10),
                 bg=COLORS["panel_bg"], fg=COLORS["text"]).pack(side=tk.LEFT, padx=(10, 5))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(control_panel, textvariable=self.search_var,
                                    font=("Microsoft YaHei", 10), width=15,
                                    bg=COLORS["input_bg"], fg=COLORS["text"],
                                    insertbackground=COLORS["text"],
                                    relief="flat", highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    highlightcolor=COLORS["info"])
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._apply_search())

        search_btn = tk.Button(control_panel, text="查找", font=("Microsoft YaHei", 10),
                              bg=COLORS["button"], fg=COLORS["text"],
                              activebackground=COLORS["button_hover"],
                              activeforeground=COLORS["text"],
                              relief="flat", cursor="hand2",
                              command=self._apply_search)
        search_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 清空按钮
        clear_btn = tk.Button(control_panel, text="清空", font=("Microsoft YaHei", 10),
                             bg=COLORS["button"], fg=COLORS["text"],
                             activebackground=COLORS["button_hover"],
                             activeforeground=COLORS["text"],
                             relief="flat", cursor="hand2",
                             command=self._clear_search)
        clear_btn.pack(side=tk.LEFT)

        # 背包物品列表
        self.inventory_frame = tk.Frame(
            right_frame,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid"
        )
        self.inventory_frame.pack(fill=tk.BOTH, expand=True)

        # 页码导航区域
        self.page_nav_frame = tk.Frame(right_frame, bg=COLORS["background"])
        # 初始不显示，有物品时才显示

        # 底部：物品信息区域
        self.info_frame = tk.Frame(
            main_container,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid",
            height=200  # 增加高度以显示更多信息
        )
        self.info_frame.pack(fill=tk.X, pady=(20, 0))
        self.info_frame.pack_propagate(False)  # 固定高度

        # 初始显示
        self._refresh_equipment()
        self._refresh_inventory()
        self._show_default_info()

    def _get_capacity_info(self) -> str:
        """获取容量信息"""
        used = self.inventory_manager.get_inventory_used()
        capacity = self.inventory_manager.get_inventory_capacity()
        free = self.inventory_manager.get_inventory_free()

        return f"{used}/{capacity} ({free} 空位)"

    def _refresh_capacity_display(self):
        """刷新容量显示"""
        if self.capacity_label:
            capacity_info = self._get_capacity_info()
            self.capacity_label.config(text=capacity_info)

    def _refresh_equipment(self):
        """刷新装备显示"""
        # 清空装备区域
        for widget in self.equipment_frame.winfo_children():
            widget.destroy()

        # 获取装备数据
        equipped_items = self.inventory_manager.get_equipped_items()

        # 创建装备槽位
        slots = [
            ("weapon", "武器"),
            ("armor", "护甲"),
            ("accessory", "饰品")
        ]

        for slot_id, slot_name in slots:
            slot_frame = tk.Frame(
                self.equipment_frame,
                bg=COLORS["card_bg"],
                highlightbackground=COLORS["border_light"],
                highlightthickness=1,
                relief="solid",
                padx=10,
                pady=10
            )
            slot_frame.pack(fill=tk.X, padx=10, pady=5)

            # 槽位名称
            slot_label = tk.Label(
                slot_frame,
                text=slot_name,
                font=("Microsoft YaHei", 12, "bold"),
                fg=COLORS["text"],
                bg=COLORS["card_bg"]
            )
            slot_label.pack(anchor=tk.W)

            # 装备物品
            item = equipped_items.get(slot_id)
            if item:
                self._create_equipment_item_display(slot_frame, item, slot_id)
            else:
                self._create_empty_slot_display(slot_frame, slot_id)

    def _create_equipment_item_display(self, parent, item: Dict[str, Any], slot_id: str):
        """创建装备物品显示"""
        item_frame = tk.Frame(parent, bg=COLORS["card_bg"])
        item_frame.pack(fill=tk.X, pady=(5, 0))

        # 物品名称和稀有度
        name = item.get("name", "未知物品")
        rarity = item.get("rarity", "common")
        rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])

        name_label = tk.Label(
            item_frame,
            text=name,
            font=("Microsoft YaHei", 11, "bold"),
            fg=rarity_color,
            bg=COLORS["card_bg"]
        )
        name_label.pack(anchor=tk.W)

        # 物品类型
        item_type = item.get("item_type", "unknown")
        type_display = ITEM_TYPES.get(item_type, item_type)

        type_label = tk.Label(
            item_frame,
            text=f"类型: {type_display}",
            font=("Microsoft YaHei", 10),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        type_label.pack(anchor=tk.W)

        # 卸下按钮
        unequip_btn = tk.Button(
            item_frame,
            text="卸下",
            font=("Microsoft YaHei", 10),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=lambda s=slot_id: self._unequip_item(s)
        )
        unequip_btn.pack(anchor=tk.W, pady=(5, 0))

        # 绑定点击事件显示详细信息，使用add='+'确保不覆盖滚轮事件
        item_frame.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')
        name_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')
        type_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')

    def _create_empty_slot_display(self, parent, slot_id: str):
        """创建空槽位显示"""
        empty_label = tk.Label(
            parent,
            text="[空]",
            font=("Microsoft YaHei", 10),
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"]
        )
        empty_label.pack(pady=(5, 0))

    def _refresh_inventory(self):
        """刷新背包显示（使用当前筛选和排序设置）"""
        self._refresh_inventory_with_filter_sort()

    def _create_inventory_item_display(self, parent, item: Dict[str, Any]) -> tk.Frame:
        """创建背包物品显示"""
        instance_id = item.get("instance_id")
        name = item.get("name", "未知物品")
        rarity = item.get("rarity", "common")
        item_type = item.get("item_type", "unknown")
        equipped = item.get("equipped", False)

        rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])
        type_display = ITEM_TYPES.get(item_type, item_type)

        # 物品框架 - 宽度150px，保持固定大小
        item_frame = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            relief="solid",
            width=160,  # 宽度160px
            height=100
        )
        item_frame.pack_propagate(False)  # 固定大小

        # 装备标记
        if equipped:
            equipped_label = tk.Label(
                item_frame,
                text="[已装备]",
                font=("Microsoft YaHei", 9),
                fg=COLORS["success"],
                bg=COLORS["card_bg"]
            )
            equipped_label.pack(anchor=tk.NE, padx=5, pady=5)

        # 物品名称
        name_label = tk.Label(
            item_frame,
            text=name,
            font=("Microsoft YaHei", 12, "bold"),
            fg=rarity_color,
            bg=COLORS["card_bg"],
            wraplength=130,
        )
        name_label.pack(pady=(15, 5))

        # 物品类型
        type_label = tk.Label(
            item_frame,
            text=type_display,
            font=("Microsoft YaHei", 10),
            fg=COLORS["text_secondary"],
            bg=COLORS["card_bg"]
        )
        type_label.pack()

        # 操作按钮框架
        button_frame = tk.Frame(item_frame, bg=COLORS["card_bg"])
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        if not equipped and item_type in ["weapon", "armor", "accessory"]:
            # 装备按钮
            equip_btn = tk.Button(
                button_frame,
                text="装备",
                font=("Microsoft YaHei", 9),
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["button_hover"],
                activeforeground=COLORS["text"],
                relief="flat",
                cursor="hand2",
                command=lambda iid=instance_id: self._equip_item(iid)
            )
            equip_btn.pack(side=tk.LEFT, padx=(0, 2), fill=tk.X, expand=True)

        # 丢弃按钮
        discard_btn = tk.Button(
            button_frame,
            text="丢弃",
            font=("Microsoft YaHei", 9),
            bg=COLORS["danger"],
            fg=COLORS["text"],
            activebackground=COLORS["danger_light"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=lambda iid=instance_id: self._discard_item(iid)
        )
        discard_btn.pack(side=tk.RIGHT, padx=(2, 0), fill=tk.X, expand=True)

        # 绑定点击事件显示详细信息，使用add='+'确保不覆盖滚轮事件
        item_frame.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')
        name_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')
        type_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i), add='+')

        return item_frame

    def _show_default_info(self):
        """显示默认信息"""
        self._clear_info_frame()

        default_label = tk.Label(
            self.info_frame,
            text="点击物品查看详细信息",
            font=("Microsoft YaHei", 12),
            fg=COLORS["text_muted"],
            bg=COLORS["panel_bg"]
        )
        default_label.pack(expand=True)

    def _show_item_info(self, item: Dict[str, Any]):
        """显示物品详细信息"""
        self._clear_info_frame()
        self.selected_item = item

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

        # 物品基本信息
        name = item.get("name", "未知物品")
        rarity = item.get("rarity", "common")
        description = item.get("description", "")
        item_type = item.get("item_type", "unknown")

        rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])
        type_display = ITEM_TYPES.get(item_type, item_type)

        # 名称和稀有度
        name_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
        name_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        name_label = tk.Label(
            name_frame,
            text=name,
            font=("Microsoft YaHei", 14, "bold"),
            fg=rarity_color,
            bg=COLORS["panel_bg"]
        )
        name_label.pack(side=tk.LEFT)

        rarity_label = tk.Label(
            name_frame,
            text=f"[{rarity}]",
            font=("Microsoft YaHei", 10),
            fg=rarity_color,
            bg=COLORS["panel_bg"]
        )
        rarity_label.pack(side=tk.RIGHT)

        # 类型
        type_label = tk.Label(
            info_content,
            text=f"类型: {type_display}",
            font=("Microsoft YaHei", 11),
            fg=COLORS["text_secondary"],
            bg=COLORS["panel_bg"]
        )
        type_label.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # 描述
        if description:
            desc_label = tk.Label(
                info_content,
                text=description,
                font=("Microsoft YaHei", 10),
                fg=COLORS["text"],
                bg=COLORS["panel_bg"],
                wraplength=INVENTORY_WINDOW_WIDTH - 80,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # 属性
        attributes = item.get("attributes", {})
        if attributes:
            attr_frame = tk.Frame(info_content, bg=COLORS["panel_bg"])
            attr_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            attr_title = tk.Label(
                attr_frame,
                text="属性:",
                font=("Microsoft YaHei", 11, "bold"),
                fg=COLORS["text"],
                bg=COLORS["panel_bg"]
            )
            attr_title.pack(anchor=tk.W)

            for attr_name, attr_value in attributes.items():
                display_name = ATTRIBUTE_DISPLAY_NAMES.get(attr_name, attr_name)
                attr_label = tk.Label(
                    attr_frame,
                    text=f"  • {display_name}: +{attr_value}",
                    font=("Microsoft YaHei", 10),
                    fg=COLORS["text_secondary"],
                    bg=COLORS["panel_bg"],
                    justify=tk.LEFT
                )
                attr_label.pack(anchor=tk.W)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_canvas(canvas, info_content)

        # 放置滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _clear_info_frame(self):
        """清空信息区域"""
        for widget in self.info_frame.winfo_children():
            widget.destroy()

    def _equip_item(self, instance_id: str):
        """装备物品"""
        success = self.inventory_manager.equip_item(instance_id)
        if success:
            self._refresh_capacity_display()
            self._refresh_equipment()
            self._refresh_inventory()
            show_toast("装备成功！", self, toast_type="success")
        else:
            show_toast("装备失败！", self, toast_type="error")

    def _unequip_item(self, slot_id: str):
        """卸下装备"""
        success = self.inventory_manager.unequip_item(slot_id)
        if success:
            self._refresh_capacity_display()
            self._refresh_equipment()
            self._refresh_inventory()
            show_toast("卸下成功！", self, toast_type="success")
        else:
            show_toast("卸下失败！", self, toast_type="error")

    def _discard_item(self, instance_id: str):
        """丢弃物品"""
        # 确认对话框（保留，因为需要用户确认）
        if not messagebox.askyesno("确认", "确定要丢弃这个物品吗？"):
            return

        success = self.inventory_manager.remove_item_from_inventory(instance_id)
        if success:
            self._refresh_capacity_display()
            self._refresh_inventory()
            self._show_default_info()
            show_toast("物品已丢弃！", self, toast_type="success")
        else:
            show_toast("丢弃失败！", self, toast_type="error")

    def _apply_filter(self, filter_type: str):
        """应用分类筛选"""
        self.current_filter = filter_type
        self.current_page = 0  # 切换筛选时回到第一页
        self._refresh_filter_buttons()
        self._refresh_inventory_with_filter_sort()

    def _refresh_filter_buttons(self):
        """刷新分类按钮状态"""
        for filter_key, button in self.filter_buttons.items():
            if filter_key == self.current_filter:
                button.config(bg=COLORS["success"])
            else:
                button.config(bg=COLORS["button"])

    def _apply_search(self):
        """应用名称查找"""
        search_text = self.search_var.get().strip()
        if search_text:
            self.current_search = search_text.lower()  # 转换为小写便于匹配
        else:
            self.current_search = None
        self.current_page = 0  # 切换搜索时回到第一页
        self._refresh_inventory_with_filter_sort()

    def _clear_search(self):
        """清空查找"""
        self.search_var.set("")
        self.current_search = None
        self.current_page = 0
        self._refresh_inventory_with_filter_sort()

    def _refresh_inventory_with_filter_sort(self, page=None):
        """使用当前筛选和排序设置刷新背包显示"""
        if page is not None:
            self.current_page = page

        # 清空背包区域
        for widget in self.inventory_frame.winfo_children():
            widget.destroy()

        # 获取筛选、搜索和排序后的物品（缓存起来）
        self._all_filtered_items = self.inventory_manager.get_filtered_sorted_items(
            filter_type=self.current_filter,
            sort_by=self.current_sort,
            search_text=self.current_search
        )
        items = self._all_filtered_items

        # 计算分页
        self.total_pages = max(1, (len(items) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE) if items else 0
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))

        # 切片当前页物品
        start_idx = self.current_page * self.ITEMS_PER_PAGE
        end_idx = min(start_idx + self.ITEMS_PER_PAGE, len(items))
        page_items = items[start_idx:end_idx]

        # 更新页码导航
        self._update_page_nav()

        # 显示搜索结果提示
        if self.current_search:
            if items:
                search_info = tk.Label(self.inventory_frame,
                                      text=f"找到 {len(items)} 个匹配 '{self.current_search}' 的物品",
                                      font=("Microsoft YaHei", 10),
                                      bg=COLORS["panel_bg"], fg=COLORS["info"])
                search_info.pack(pady=(5, 10))
            else:
                no_results = tk.Label(self.inventory_frame,
                                     text=f"未找到匹配 '{self.current_search}' 的物品",
                                     font=("Microsoft YaHei", 10),
                                     bg=COLORS["panel_bg"], fg=COLORS["warning"])
                no_results.pack(pady=(20, 20))
                return

        if not items:
            empty_label = tk.Label(
                self.inventory_frame,
                text="背包空空如也" if self.current_filter == "all" else f"没有{self._get_filter_display_name()}物品",
                font=("Microsoft YaHei", 14),
                fg=COLORS["text_muted"],
                bg=COLORS["panel_bg"]
            )
            empty_label.pack(expand=True)
            return

        # 页面提示
        if self.total_pages > 1:
            page_info = tk.Label(self.inventory_frame,
                                text=f"第 {self.current_page + 1}/{self.total_pages} 页，共 {len(items)} 件物品",
                                font=("Microsoft YaHei", 10),
                                bg=COLORS["panel_bg"], fg=COLORS["text_secondary"])
            page_info.pack(pady=(5, 5))

        # 创建滚动区域
        canvas = tk.Canvas(
            self.inventory_frame,
            bg=COLORS["panel_bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.inventory_frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg=COLORS["panel_bg"])

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_canvas(canvas, scrollable_frame)

        # 网格布局 - 5列
        items_per_row = 5
        page_item_count = len(page_items)

        # 计算总行数
        total_rows = max(1, (page_item_count + items_per_row - 1) // items_per_row)

        # 预先配置所有列和行的权重
        for col in range(items_per_row):
            scrollable_frame.grid_columnconfigure(col, weight=1, uniform="col")
        for row in range(total_rows):
            scrollable_frame.grid_rowconfigure(row, weight=1, uniform="row")

        # 放置物品（仅当前页）
        for i, item in enumerate(page_items):
            row = i // items_per_row
            col = i % items_per_row
            item_frame = self._create_inventory_item_display(scrollable_frame, item)
            item_frame.grid(row=row, column=col, padx=5, pady=10, sticky="nsew")

        # 所有物品创建完毕后，再绑定Configure事件和更新scrollregion
        scrollable_frame.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(scrollregion=canvas.bbox("all"))

        # 放置滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _get_filter_display_name(self) -> str:
        """获取筛选类型的显示名称"""
        filter_names = {
            "all": "全部",
            "weapon": "武器",
            "armor": "护甲",
            "accessory": "饰品"
        }
        return filter_names.get(self.current_filter, "未知")

    def _update_page_nav(self):
        """更新页码导航按钮"""
        # 清空导航区域
        for widget in self.page_nav_frame.winfo_children():
            widget.destroy()

        if self.total_pages <= 1:
            self.page_nav_frame.pack_forget()
            return

        self.page_nav_frame.pack(fill=tk.X, pady=(5, 0))

        # 上一页按钮
        prev_btn = tk.Button(
            self.page_nav_frame,
            text="◀ 上一页",
            font=("Microsoft YaHei", 10),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            state=tk.NORMAL if self.current_page > 0 else tk.DISABLED,
            command=lambda: self._refresh_inventory_with_filter_sort(self.current_page - 1)
        )
        prev_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 页码信息
        page_label = tk.Label(
            self.page_nav_frame,
            text=f"第 {self.current_page + 1} / {self.total_pages} 页",
            font=("Microsoft YaHei", 11),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        page_label.pack(side=tk.LEFT, padx=(10, 10))

        # 下一页按钮
        next_btn = tk.Button(
            self.page_nav_frame,
            text="下一页 ▶",
            font=("Microsoft YaHei", 10),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED,
            command=lambda: self._refresh_inventory_with_filter_sort(self.current_page + 1)
        )
        next_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 页码跳转输入
        tk.Label(self.page_nav_frame, text="跳转:",
                font=("Microsoft YaHei", 10), bg=COLORS["background"],
                fg=COLORS["text"]).pack(side=tk.LEFT, padx=(20, 5))

        page_entry = tk.Entry(
            self.page_nav_frame,
            font=("Microsoft YaHei", 10),
            width=5,
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        )
        page_entry.pack(side=tk.LEFT, padx=(0, 5))

        def go_to_page():
            try:
                target = int(page_entry.get()) - 1
                if 0 <= target < self.total_pages:
                    self._refresh_inventory_with_filter_sort(target)
            except ValueError:
                pass

        page_entry.bind("<Return>", lambda e: go_to_page())

        go_btn = tk.Button(
            self.page_nav_frame,
            text="跳转",
            font=("Microsoft YaHei", 10),
            bg=COLORS["button"],
            fg=COLORS["text"],
            activebackground=COLORS["button_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            command=go_to_page
        )
        go_btn.pack(side=tk.LEFT)

    def refresh_all(self):
        """刷新所有显示"""
        self._refresh_capacity_display()
        self._refresh_equipment()
        self._refresh_inventory()
        self._show_default_info()

    def _open_smelting(self):
        """打开熔炼界面"""
        if self.on_smelting:
            self.on_smelting()