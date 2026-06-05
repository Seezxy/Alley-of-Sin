"""
角色选择界面 - 动态读取 CHARACTERS，支持多角色
"""

from tkinter import Frame, Label as TkLabel, Canvas, Scrollbar
from game.constants import COLORS, CHARACTERS
from game.utils import create_button, create_header_label, create_label, load_image
from game.background_fill import fill_background_with_image
from game.inventory import get_inventory_manager
from game.wheel_utils import bind_mouse_wheel_to_canvas, bind_mouse_wheel_to_widget_for_canvas
from game.attribute_utils import get_attribute_utils
from game.save_crypto import _is_dev_mode


class CharacterSelect(Frame):

    def __init__(self, root, on_confirm, on_back, on_inventory=None, on_dev_panel=None):
        super().__init__(root, bg=COLORS["background"])
        self.on_confirm   = on_confirm
        self.on_back      = on_back
        self.on_inventory = on_inventory  # 背包回调
        self.on_dev_panel = on_dev_panel  # 开发者面板回调
        self.selected_key = None
        self.confirm_btn  = None
        self.detail_frame = None
        self._canvas = None
        self._setup_ui()

    def _setup_ui(self):
        # 添加背景图片
        self._canvas = fill_background_with_image(
            self, "bg_menu.jpeg", "#404040"  # 中灰色，避免黑色闪烁
        )

        # 外层容器 - 用于居中
        outer_container = Frame(self, bg=COLORS["background"])
        outer_container.pack(fill="both", expand=True)

        # 主容器 - 居中显示，限制最大宽度
        main_container = Frame(outer_container, bg=COLORS["background"])
        main_container.pack(expand=True, padx=20, pady=24)  # 增加20%

        # 限制主容器最大宽度
        main_container.config(width=840)  # 设置最大宽度（增加20%）

        # 标题
        create_header_label(main_container, "选择你的角色", font_size=36).pack(pady=(0, 24))  # 增加20%

        # 角色按钮区域
        button_container = Frame(main_container, bg=COLORS["background"])
        button_container.pack(pady=(0, 24))  # 增加20%

        # 角色按钮 - 全部放在一行
        button_row_frame = Frame(button_container, bg=COLORS["background"])
        button_row_frame.pack()

        # 所有角色键
        all_keys = ["loulo", "taiquan", "dashou", "thief", "programmer"]

        for key in all_keys:
            if key in CHARACTERS:
                create_button(
                    button_row_frame, CHARACTERS[key]["name"], width=15, height=2,
                    command=lambda k=key: self._select(k)
                ).pack(side="left", padx=8, pady=4)

        # 详细信息区域 - 使用更大的可滚动区域，带暗紫色边框
        detail_border_frame = Frame(main_container, bg=COLORS["dark_purple"], bd=3, relief="solid")
        detail_border_frame.pack(fill="both", expand=True, pady=(0, 24))  # 增加20%

        detail_container = Frame(detail_border_frame, bg=COLORS["background"])
        detail_container.pack(fill="both", expand=True, padx=2, pady=2)  # 内边距，让边框可见

        # 创建Canvas和Scrollbar
        self.detail_canvas = Canvas(detail_container, bg=COLORS["background"], highlightthickness=0, width=780, height=450)
        scrollbar = Scrollbar(detail_container, orient="vertical", command=self.detail_canvas.yview)

        # 创建可滚动的Frame
        self.detail_frame = Frame(self.detail_canvas, bg=COLORS["background"])

        # 配置Canvas
        self.detail_canvas.create_window((0, 0), window=self.detail_frame, anchor="nw")
        self.detail_canvas.configure(yscrollcommand=scrollbar.set)

        # 确保Canvas有足够的宽度
        def configure_canvas(event):
            # 限制内部frame的宽度不超过Canvas宽度
            self.detail_canvas.itemconfig(1, width=min(event.width, 780))

        self.detail_canvas.bind("<Configure>", configure_canvas)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_canvas(self.detail_canvas, self.detail_frame)

        # 放置Canvas和Scrollbar
        self.detail_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 占位，保持布局稳定
        create_label(self.detail_frame, "请选择一个角色查看详细信息", 14, COLORS["text_muted"]).pack(pady=20)

        # 按钮区域
        btn_container = Frame(main_container, bg=COLORS["background"])
        btn_container.pack()

        self.confirm_btn = create_button(
            btn_container, "确认选择", width=20, height=2,
            bg=COLORS["success"], command=self._confirm
        )
        self.confirm_btn.pack(side="left", padx=10)
        self.confirm_btn.config(state="disabled")

        create_button(
            btn_container, "返回", width=15, height=2,
            command=self.on_back
        ).pack(side="left", padx=10)

        # 左下角背包按钮
        self._add_inventory_button()

    def _select(self, key):
        self.selected_key = key
        info = CHARACTERS[key]

        for w in self.detail_frame.winfo_children():
            w.destroy()

        # 角色头像（自动探测扩展名）
        img = None
        for ext in ("png", "jpg", "jpeg"):
            img = load_image(f"char_{key}.{ext}", (100, 140))  # 稍微缩小头像
            if img:
                break

        # 角色名称和头像在同一行 - 居中显示
        name_container = Frame(self.detail_frame, bg=COLORS["background"])
        name_container.pack(pady=(0, 10))

        # 创建居中的内部框架
        name_frame = Frame(name_container, bg=COLORS["background"])
        name_frame.pack()

        if img:
            lbl = TkLabel(name_frame, image=img, bg=COLORS["background"])
            lbl.image = img  # 防止被GC
            lbl.pack(side="left", padx=(0, 15))
            bind_mouse_wheel_to_widget_for_canvas(lbl, self.detail_canvas)

        name_label = create_label(name_frame, info["name"], 22, COLORS["warning"])
        name_label.pack(side="left")
        bind_mouse_wheel_to_widget_for_canvas(name_label, self.detail_canvas)

        # 角色描述，限制宽度并自动换行 - 居中显示
        desc_container = Frame(self.detail_frame, bg=COLORS["background"])
        desc_container.pack(pady=(0, 15), fill="x")

        desc_label = TkLabel(desc_container, text=info["desc"],
                fg=COLORS["text"], bg=COLORS["background"],
                font=("Microsoft YaHei", 12), wraplength=600,  # 增加20%
                anchor="center", justify="center")
        desc_label.pack()
        bind_mouse_wheel_to_widget_for_canvas(desc_label, self.detail_canvas)

        # 获取装备属性
        inventory_manager = get_inventory_manager()
        equipment_attrs = inventory_manager.get_equipment_attributes()

        # 计算最终属性（基础属性 + 装备属性）
        final_max_hp = info['max_hp'] + equipment_attrs.get('max_hp', 0)
        final_crit_rate = info['crit_rate'] + equipment_attrs.get('crit_rate', 0)
        final_crit_damage = info['crit_damage'] + equipment_attrs.get('crit_damage', 0)
        final_damage_bonus = info['damage_bonus'] + equipment_attrs.get('damage_bonus', 0)
        final_lifesteal = info['lifesteal'] + equipment_attrs.get('lifesteal', 0)
        final_damage_reduction = info['damage_reduction'] + equipment_attrs.get('damage_reduction', 0)
        final_dodge_chance = info['dodge_chance'] + equipment_attrs.get('dodge_chance', 0)

        # 显示基础角色属性 - 分成多行显示
        base_attr_container = Frame(self.detail_frame, bg=COLORS["background"])
        base_attr_container.pack(pady=(10, 5), fill="x")

        base_attr_label = create_label(base_attr_container, "👤 基础角色属性:", 14, COLORS["text_muted"])
        base_attr_label.pack()
        bind_mouse_wheel_to_widget_for_canvas(base_attr_label, self.detail_canvas)

        # 第一行：HP、暴击率、暴击伤害 - 居中显示
        attr_container1 = Frame(self.detail_frame, bg=COLORS["background"])
        attr_container1.pack(pady=2, fill="x")

        attr_frame1 = Frame(attr_container1, bg=COLORS["background"])
        attr_frame1.pack()

        hp_label = create_label(attr_frame1, f"❤️  HP：{info['max_hp']}", 12, COLORS["text_muted"])
        hp_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(hp_label, self.detail_canvas)

        crit_rate_label = create_label(attr_frame1, f"💥  暴击率：{info['crit_rate']*100:.0f}%", 12, COLORS["text_muted"])
        crit_rate_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(crit_rate_label, self.detail_canvas)

        crit_damage_label = create_label(attr_frame1, f"🔥  暴击伤害：+{info['crit_damage']*100:.0f}%", 12, COLORS["text_muted"])
        crit_damage_label.pack(side="left")
        bind_mouse_wheel_to_widget_for_canvas(crit_damage_label, self.detail_canvas)

        # 第二行：伤害加成、吸血、免伤、闪避 - 居中显示
        attr_container2 = Frame(self.detail_frame, bg=COLORS["background"])
        attr_container2.pack(pady=2, fill="x")

        attr_frame2 = Frame(attr_container2, bg=COLORS["background"])
        attr_frame2.pack()

        damage_bonus_label = create_label(attr_frame2, f"⚔️  伤害加成：{info['damage_bonus']*100:.0f}%", 12, COLORS["text_muted"])
        damage_bonus_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(damage_bonus_label, self.detail_canvas)

        lifesteal_label = create_label(attr_frame2, f"🩸  吸血：{info['lifesteal']*100:.0f}%", 12, COLORS["text_muted"])
        lifesteal_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(lifesteal_label, self.detail_canvas)

        damage_reduction_label = create_label(attr_frame2, f"🛡️  免伤：{info['damage_reduction']*100:.0f}%", 12, COLORS["text_muted"])
        damage_reduction_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(damage_reduction_label, self.detail_canvas)

        dodge_chance_label = create_label(attr_frame2, f"💨  闪避：{info['dodge_chance']*100:.0f}%", 12, COLORS["text_muted"])
        dodge_chance_label.pack(side="left")
        bind_mouse_wheel_to_widget_for_canvas(dodge_chance_label, self.detail_canvas)

        # 总是显示最终属性，但根据是否有装备使用不同的标题和颜色
        final_attr_container = Frame(self.detail_frame, bg=COLORS["background"])
        final_attr_container.pack(pady=(15, 5), fill="x")

        if equipment_attrs:
            final_attr_label = create_label(final_attr_container, "🎯 装备加成后最终属性:", 14, COLORS["highlight"])
            attr_color = COLORS["success"]
        else:
            final_attr_label = create_label(final_attr_container, "📊 当前属性:", 14, COLORS["text"])
            attr_color = COLORS["text_secondary"]

        final_attr_label.pack()
        bind_mouse_wheel_to_widget_for_canvas(final_attr_label, self.detail_canvas)

        # 第一行：HP、暴击率、暴击伤害 - 居中显示
        final_container1 = Frame(self.detail_frame, bg=COLORS["background"])
        final_container1.pack(pady=2, fill="x")

        final_frame1 = Frame(final_container1, bg=COLORS["background"])
        final_frame1.pack()

        final_hp_label = create_label(final_frame1, f"❤️  HP：{final_max_hp:.1f}", 12, attr_color)
        final_hp_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(final_hp_label, self.detail_canvas)

        final_crit_rate_label = create_label(final_frame1, f"💥  暴击率：{final_crit_rate*100:.0f}%", 12, attr_color)
        final_crit_rate_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(final_crit_rate_label, self.detail_canvas)

        final_crit_damage_label = create_label(final_frame1, f"🔥  暴击伤害：+{final_crit_damage*100:.0f}%", 12, attr_color)
        final_crit_damage_label.pack(side="left")
        bind_mouse_wheel_to_widget_for_canvas(final_crit_damage_label, self.detail_canvas)

        # 第二行：伤害加成、吸血、免伤、闪避 - 居中显示
        final_container2 = Frame(self.detail_frame, bg=COLORS["background"])
        final_container2.pack(pady=2, fill="x")

        final_frame2 = Frame(final_container2, bg=COLORS["background"])
        final_frame2.pack()

        final_damage_bonus_label = create_label(final_frame2, f"⚔️  伤害加成：{final_damage_bonus*100:.0f}%", 12, attr_color)
        final_damage_bonus_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(final_damage_bonus_label, self.detail_canvas)

        final_lifesteal_label = create_label(final_frame2, f"🩸  吸血：{final_lifesteal*100:.0f}%", 12, attr_color)
        final_lifesteal_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(final_lifesteal_label, self.detail_canvas)

        final_damage_reduction_label = create_label(final_frame2, f"🛡️  免伤：{final_damage_reduction*100:.0f}%", 12, attr_color)
        final_damage_reduction_label.pack(side="left", padx=(0, 15))
        bind_mouse_wheel_to_widget_for_canvas(final_damage_reduction_label, self.detail_canvas)

        final_dodge_chance_label = create_label(final_frame2, f"💨  闪避：{final_dodge_chance*100:.0f}%", 12, attr_color)
        final_dodge_chance_label.pack(side="left")
        bind_mouse_wheel_to_widget_for_canvas(final_dodge_chance_label, self.detail_canvas)

        # 如果有装备加成，显示装备加成详情
        if equipment_attrs:
            equipment_detail_container = Frame(self.detail_frame, bg=COLORS["background"])
            equipment_detail_container.pack(pady=(15, 8), fill="x")

            equipment_detail_label = create_label(equipment_detail_container, "📊 装备加成详情:", 12, COLORS["info"])
            equipment_detail_label.pack()
            bind_mouse_wheel_to_widget_for_canvas(equipment_detail_label, self.detail_canvas)

            # 创建网格框架 - 居中显示
            grid_container = Frame(self.detail_frame, bg=COLORS["background"])
            grid_container.pack(fill="x")

            grid_frame = Frame(grid_container, bg=COLORS["background"])
            grid_frame.pack()

            # 定义显示名称映射
            display_names = {
                'max_hp': '最大生命值',
                'damage_bonus': '伤害加成',
                'crit_rate': '暴击率',
                'crit_damage': '暴击伤害',
                'lifesteal': '生命偷取',
                'damage_reduction': '伤害减免',
                'dodge_chance': '闪避几率'
            }

            # 显示所有有加成的属性
            row = 0
            col = 0
            attribute_utils = get_attribute_utils()

            for attr_name, attr_value in equipment_attrs.items():
                if attr_value != 0:
                    display_name = attribute_utils.get_attribute_display_name(attr_name)
                    value_str = attribute_utils.format_attribute(attr_name, attr_value)

                    # 创建属性标签框架
                    attr_frame = Frame(grid_frame, bg=COLORS["background"])
                    attr_frame.grid(row=row, column=col, padx=10, pady=3, sticky="w")

                    attr_name_label = create_label(attr_frame, f"{display_name}:", 11, COLORS["text_secondary"])
                    attr_name_label.pack(side="left")
                    bind_mouse_wheel_to_widget_for_canvas(attr_name_label, self.detail_canvas)

                    attr_value_label = create_label(attr_frame, value_str, 11, COLORS["info"])
                    attr_value_label.pack(side="left", padx=(5, 0))
                    bind_mouse_wheel_to_widget_for_canvas(attr_value_label, self.detail_canvas)

                    col += 1
                    if col >= 3:  # 每行显示3个属性
                        col = 0
                        row += 1

        # 更新Canvas的滚动区域
        self.detail_frame.update_idletasks()
        if hasattr(self, 'detail_canvas') and self.detail_canvas:
            # 获取内容的实际大小
            self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))
            # 确保Canvas可以滚动
            self.detail_canvas.yview_moveto(0)

        self.confirm_btn.config(state="normal")

    def _confirm(self):
        if self.selected_key:
            self.on_confirm(self.selected_key)

    def _add_inventory_button(self):
        """在左下角添加背包按钮"""
        from game.utils import create_button
        inventory_button = create_button(
            self, "背包", width=10, height=2,
            command=self._on_inventory
        )
        # 放置在左下角
        inventory_button.place(relx=0.02, rely=0.95, anchor="sw")

        # 开发者按钮（仅开发者模式可见）
        if _is_dev_mode() and self.on_dev_panel:
            dev_btn = create_button(
                self, "🔧 开发者", width=10, height=2,
                command=self._on_dev_panel
            )
            dev_btn.place(relx=0.12, rely=0.95, anchor="sw")

    def _on_dev_panel(self):
        """打开开发者面板"""
        if self.on_dev_panel:
            self.on_dev_panel()
    def _on_inventory(self):
        """打开背包界面"""
        if self.on_inventory:
            self.on_inventory()
        else:
            # 回退到旧方法（打开新窗口）
            # 导入放在这里避免循环导入
            from game.item_ui import InventoryWindow

            # 创建背包窗口
            inventory_window = InventoryWindow(self.master)
            inventory_window.grab_set()  # 模态窗口
