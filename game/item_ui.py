"""
背包界面模块
负责背包界面的显示和交互
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
from game.smelting_ui import SmeltingWindow
from game.toast import show_toast


class InventoryWindow(tk.Toplevel):
    """背包窗口"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(INVENTORY_WINDOW_TITLE)
        self.geometry(f"{INVENTORY_WINDOW_WIDTH}x{INVENTORY_WINDOW_HEIGHT}")
        self.configure(bg=COLORS["background"])
        self.resizable(False, False)

        # 获取管理器实例
        self.inventory_manager = get_inventory_manager()
        self.item_manager = get_item_manager()

        # 界面组件
        self.equipment_frame = None
        self.inventory_frame = None
        self.info_frame = None
        self.selected_item = None

        self._setup_ui()

    def _setup_ui(self):
        """设置界面布局"""
        # 主容器
        main_container = tk.Frame(self, bg=COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            main_container,
            text="背 包",
            font=("Microsoft YaHei", 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        title_label.pack(pady=(0, 20))

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
        inventory_header.pack(fill=tk.X, pady=(0, 10))

        # 左侧：背包标题
        title_frame = tk.Frame(inventory_header, bg=COLORS["background"])
        title_frame.pack(side=tk.LEFT, anchor=tk.W)

        inventory_label = tk.Label(
            title_frame,
            text="背 包",
            font=("Microsoft YaHei", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        )
        inventory_label.pack(side=tk.LEFT)

        # 熔炼按钮 - 使用更明显的样式
        smelting_btn = tk.Button(
            title_frame,
            text="🔥 熔炼",
            font=("Microsoft YaHei", 11, "bold"),
            bg=COLORS["warning"],
            fg=COLORS["text"],
            activebackground=COLORS["warning_light"],
            activeforeground=COLORS["text"],
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self._open_smelting_window,
            padx=10,
            pady=2
        )
        smelting_btn.pack(side=tk.LEFT, padx=(15, 0))

        # 右侧：容量信息
        capacity_info = self._get_capacity_info()
        capacity_label = tk.Label(
            inventory_header,
            text=capacity_info,
            font=("Microsoft YaHei", 12),
            fg=COLORS["text_secondary"],
            bg=COLORS["background"]
        )
        capacity_label.pack(side=tk.RIGHT, anchor=tk.E)

        # 背包物品列表
        self.inventory_frame = tk.Frame(
            right_frame,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid"
        )
        self.inventory_frame.pack(fill=tk.BOTH, expand=True)

        # 底部：物品信息区域
        self.info_frame = tk.Frame(
            main_container,
            bg=COLORS["panel_bg"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid",
            height=150
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

        # 绑定点击事件显示详细信息
        item_frame.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))
        name_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))
        type_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))

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
        """刷新背包显示"""
        # 清空背包区域
        for widget in self.inventory_frame.winfo_children():
            widget.destroy()

        # 获取背包物品
        items = self.inventory_manager.get_inventory_items()

        if not items:
            # 显示空背包信息
            empty_label = tk.Label(
                self.inventory_frame,
                text="背包空空如也",
                font=("Microsoft YaHei", 14),
                fg=COLORS["text_muted"],
                bg=COLORS["panel_bg"]
            )
            empty_label.pack(expand=True)
            return

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

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 网格布局
        items_per_row = 4
        for i, item in enumerate(items):
            row = i // items_per_row
            col = i % items_per_row

            item_frame = self._create_inventory_item_display(scrollable_frame, item)
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # 配置网格权重
            scrollable_frame.grid_columnconfigure(col, weight=1)

        # 放置滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_inventory_item_display(self, parent, item: Dict[str, Any]) -> tk.Frame:
        """创建背包物品显示"""
        instance_id = item.get("instance_id")
        name = item.get("name", "未知物品")
        rarity = item.get("rarity", "common")
        item_type = item.get("item_type", "unknown")
        equipped = item.get("equipped", False)

        rarity_color = RARITY_COLORS.get(rarity, COLORS["text"])
        type_display = ITEM_TYPES.get(item_type, item_type)

        # 物品框架
        item_frame = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
            relief="solid",
            width=150,
            height=100
        )
        item_frame.pack_propagate(False)  # 固定大小

        # 装备标记
        if equipped:
            equipped_label = tk.Label(
                item_frame,
                text="[已装备]",
                font=("Microsoft YaHei", 8),
                fg=COLORS["success"],
                bg=COLORS["card_bg"]
            )
            equipped_label.pack(anchor=tk.NE, padx=5, pady=5)

        # 物品名称
        name_label = tk.Label(
            item_frame,
            text=name,
            font=("Microsoft YaHei", 10, "bold"),
            fg=rarity_color,
            bg=COLORS["card_bg"],
            wraplength=130
        )
        name_label.pack(pady=(15, 5))

        # 物品类型
        type_label = tk.Label(
            item_frame,
            text=type_display,
            font=("Microsoft YaHei", 9),
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

        # 绑定点击事件显示详细信息
        item_frame.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))
        name_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))
        type_label.bind("<Button-1>", lambda e, i=item: self._show_item_info(i))

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
            self._refresh_equipment()
            self._refresh_inventory()
            show_toast("装备成功！", self, toast_type="success")
        else:
            show_toast("装备失败！", self, toast_type="error")

    def _unequip_item(self, slot_id: str):
        """卸下装备"""
        success = self.inventory_manager.unequip_item(slot_id)
        if success:
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
            self._refresh_inventory()
            self._show_default_info()
            show_toast("物品已丢弃！", self, toast_type="success")
        else:
            show_toast("丢弃失败！", self, toast_type="error")

    def refresh_all(self):
        """刷新所有显示"""
        self._refresh_equipment()
        self._refresh_inventory()
        self._show_default_info()

    def _open_smelting_window(self):
        """打开熔炼窗口"""
        smelting_window = SmeltingWindow(self)
        smelting_window.grab_set()  # 模态窗口