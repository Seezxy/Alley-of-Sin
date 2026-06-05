"""
卡牌对战 UI - 罪恶巷口
负责界面渲染和用户交互，游戏逻辑见 models.py
"""

import tkinter as tk
from tkinter import Frame, Label, Button, Text, Scrollbar, messagebox
import random
import time

from game.constants import COLORS, CHARACTERS
from game.models import (
    Card, Deck, Player, DamageContext, PositionBattleLogic,
    INITIAL_HP, INITIAL_HAND, DRAW_PER_TURN
)
from game.utils import load_image
from game.inventory import get_inventory_manager
from game.wheel_utils import bind_mouse_wheel_to_canvas, bind_mouse_wheel_to_text
from game.toast import show_toast



# 牌面图片缓存（card_type -> PhotoImage）
_CARD_IMAGES = {}

def _get_card_image(card_type):
    """获取牌面图片，自动探测扩展名，缓存复用"""
    if card_type not in _CARD_IMAGES:
        img = None
        for ext in ("jpg", "jpeg", "png"):
            img = load_image(f"card_{card_type}.{ext}", (56, 80))
            if img:
                break
        _CARD_IMAGES[card_type] = img
    return _CARD_IMAGES[card_type]

# ==================== 局部 UI 工具函数 ====================

def create_button(parent, text, width=10, height=1, bg=None, fg="white", command=None):
    bg = bg or COLORS["button"]
    return Button(parent, text=text, width=width, height=height,
                  bg=bg, fg=fg, font=("微软雅黑", 12), command=command)

def create_label(parent, text, font_size=12, fg=None, bg=None):
    fg = fg or COLORS["text"]
    bg = bg or COLORS["background"]
    return Label(parent, text=text, font=("微软雅黑", font_size),
                 bg=bg, fg=fg, justify="center")

def create_header_label(parent, text, font_size=24, fg=None, bg=None):
    fg = fg or COLORS["warning"]
    bg = bg or COLORS["background"]
    return Label(parent, text=text, font=("微软雅黑", font_size, "bold"),
                 bg=bg, fg=fg, justify="center")


# ==================== 主战斗界面 ====================

class CardBattle(Frame):

    def __init__(self, root, on_win=None, on_lose=None,
                 character_key=None, initial_attrs=None, is_final=False, ai_attrs=None, difficulty=1, is_endless_mode=False, endless_mode_instance=None):
        super().__init__(root, bg=COLORS["background"])
        self.on_win   = on_win
        self.on_lose  = on_lose
        self.root     = root
        self.is_final = is_final
        self.ai_attrs = ai_attrs or {}  # 本场 AI 属性配置
        self.difficulty = difficulty  # 难度级别：0=简单,1=标准,2=困难,3=地狱
        self.is_endless_mode = is_endless_mode  # 无尽模式标记
        self.endless_mode_instance = endless_mode_instance  # 无尽模式实例（用于结束战斗）

        self.selected_character  = None
        self.character_config    = None
        self.player_attrs_to_keep = {}

        self.turn          = 1
        self.phase         = "place"
        self.selected_card = None

        # 难度级别映射
        self.difficulty_names = {
            0: "简单",
            1: "标准",
            2: "困难",
            3: "地狱"
        }

        if character_key:
            self.selected_character = character_key
            self.character_config   = CHARACTERS[character_key]
            if initial_attrs:
                self.player_attrs_to_keep = initial_attrs.copy()
            self._init_players()
            self._setup_ui()
            self._reset_battle_state()
        else:
            # 独立运行时不再弹出角色选择，使用默认角色
            self.selected_character = "loulo"
            self.character_config = CHARACTERS["loulo"]
            show_toast("使用默认角色：喽啰", self, toast_type="info")

    # ==================== 初始化 ====================

    # 角色选择弹窗已移除，现在使用集成的角色选择流程
        self._init_players()
        self._setup_ui()
        self._reset_battle_state()

    def _init_players(self):
        """创建玩家和 AI，各自独立牌库"""
        if not self.character_config:
            self.character_config = CHARACTERS["loulo"]

        self.player      = Player("玩家")
        self.player.deck = Deck(self.character_config.get("deck"))
        self.ai          = Player("电脑")
        self.ai.deck     = Deck()

        # 获取装备属性
        inventory_manager = get_inventory_manager()
        equipment_attrs = inventory_manager.get_equipment_attributes()

        cfg = self.character_config

        # 如果有保存的属性，使用保存的属性
        if self.player_attrs_to_keep:
            for k, v in self.player_attrs_to_keep.items():
                setattr(self.player, k, v)
        else:
            # 否则使用基础角色属性
            self.player.damage_bonus     = cfg["damage_bonus"]
            self.player.lifesteal        = cfg["lifesteal"]
            self.player.damage_reduction = cfg["damage_reduction"]
            self.player.dodge_chance     = cfg["dodge_chance"]
            self.player.crit_rate        = cfg["crit_rate"]
            self.player.crit_damage      = cfg["crit_damage"]
            self.player.max_hp           = cfg["max_hp"]

        # 确保HP不超过最大HP
        self.player.hp = min(self.player.hp, self.player.max_hp) if hasattr(self.player, 'hp') else self.player.max_hp

        # 总是应用装备属性加成（保存的属性不再包含装备加成）
        if equipment_attrs:
            for attr_name, attr_value in equipment_attrs.items():
                if hasattr(self.player, attr_name):
                    current_value = getattr(self.player, attr_name)
                    # 根据属性类型进行加法或乘法
                    if attr_name in ["damage_bonus", "lifesteal", "damage_reduction",
                                   "dodge_chance", "crit_rate", "crit_damage"]:
                        # 百分比属性：加法
                        setattr(self.player, attr_name, current_value + attr_value)
                    elif attr_name == "max_hp":
                        # 生命值：加法
                        setattr(self.player, attr_name, current_value + attr_value)
                        self.player.hp = self.player.max_hp  # 更新当前HP
                    else:
                        # 其他属性：直接设置
                        setattr(self.player, attr_name, attr_value)

        # 确保玩家免伤不超过0.99
        if hasattr(self.player, 'damage_reduction') and self.player.damage_reduction > 0.99:
            self.player.damage_reduction = 0.99

        self.ai.max_hp = self.ai_attrs.get("max_hp", INITIAL_HP)
        self.ai.hp     = self.ai.max_hp
        for attr in ("damage_bonus", "damage_reduction", "crit_rate",
                     "crit_damage", "lifesteal", "dodge_chance"):
            if attr in self.ai_attrs:
                setattr(self.ai, attr, self.ai_attrs[attr])

        # 确保AI免伤不超过0.99
        if hasattr(self.ai, 'damage_reduction') and self.ai.damage_reduction > 0.99:
            self.ai.damage_reduction = 0.99

        self.player.draw_cards(INITIAL_HAND)
        self.ai.draw_cards(INITIAL_HAND)

    def _reset_battle_state(self):
        """重置战斗（保留强化属性）"""
        if not hasattr(self, "player"):
            self._init_players()

        self.player.hp = self.player.max_hp
        self.ai.hp     = self.ai.max_hp

        self.player.deck = Deck(self.character_config.get("deck") if self.character_config else None)
        self.ai.deck     = Deck()

        self.player.hand  = []
        self.ai.hand      = []
        self.player.slots = [None] * 5
        self.ai.slots     = [None] * 5

        self.player.draw_cards(INITIAL_HAND)
        self.ai.draw_cards(INITIAL_HAND)

        self.turn          = 1
        self.phase         = "place"
        self.selected_card = None

        if hasattr(self, "p_hp_label") and hasattr(self, "player_slots") and self.player_slots:
            self._update_hp_display()
            self._update_slot_display()
            self._update_hand_display()
            self._clear_logs()
            self._add_log(f"战斗开始！角色：{self.character_config['name']}")
            self._refresh_attr_panel()

    # ==================== UI 构建 ====================

    def _setup_ui(self):
        """place 百分比布局：左属性(14%) | 中战斗(72%) | 右结算(14%)"""

        # 顶部信息栏
        self.top = Frame(self, bg=COLORS["background"])
        self.top.place(relx=0, rely=0, relwidth=1, height=45)

        # 如果是无尽模式，添加额外信息显示
        if self.is_endless_mode:
            self._add_endless_info_display()

        self.turn_label = create_label(self.top, "第 1 回合", 14, COLORS["warning"])
        self.turn_label.pack(side="left", padx=10)
        self.char_label = create_label(self.top, f"🎭 {self.character_config['name']}", 14, COLORS["info"])
        self.char_label.pack(side="left", padx=10)
        self.p_hp_label = create_label(self.top, f"❤️ 玩家：{self.player.max_hp}", 14, COLORS["success"])
        self.p_hp_label.pack(side="left", padx=20)
        self.ai_hp_label = create_label(self.top, f"🤖 电脑：{INITIAL_HP}", 14, COLORS["danger"])
        self.ai_hp_label.pack(side="left", padx=20)

        # 难度显示
        difficulty_name = self.difficulty_names.get(self.difficulty, "标准")
        self.difficulty_label = create_label(self.top, f"难度：{difficulty_name}", 12, COLORS["warning"])
        self.difficulty_label.pack(side="left", padx=20)

        self.ai_hand_label = create_label(self.top, "手牌：6张", 12, COLORS["text"])
        self.ai_hand_label.pack(side="left", padx=20)
        create_button(self.top, "📜 规则", 8, 1, COLORS["info"],
                      command=self._show_rules).pack(side="right", padx=10)

        # 左侧属性面板
        self.left = Frame(self, bg=COLORS["panel_bg"], relief="solid", bd=1)
        self.left.place(relx=0.00, rely=0, relwidth=0.21, relheight=1, y=50, height=-105)

        create_label(self.left, "📊 双方属性", 13, COLORS["warning"]).pack(pady=(10, 4))
        self.attr_content_frame = Frame(self.left, bg=COLORS["panel_bg"])
        self.attr_content_frame.pack(fill="x", padx=10, pady=5)

        # 中间战斗区
        self.mid = Frame(self, bg=COLORS["background"])
        self.mid.place(relx=0.21, rely=0, relwidth=0.58, relheight=1, y=50, height=-105)
        self._build_mid(self.mid)

        # 右侧面板（包含结算和信息显示）
        self.right = Frame(self, bg=COLORS["background"])
        self.right.place(relx=0.79, rely=0, relwidth=0.21, relheight=1, y=50, height=-105)

        # 使用grid布局：3行，第1行结算标题，第2行结算内容，第3行信息显示
        self.right.grid_rowconfigure(1, weight=1)  # 结算内容区域可扩展
        self.right.grid_rowconfigure(2, weight=0)  # 信息显示区域固定高度
        self.right.grid_columnconfigure(0, weight=1)

        # 结算标题
        create_label(self.right, "🎬 结算过程", 13, COLORS["info"]).grid(row=0, column=0, pady=(4, 2))

        # 结算内容区域
        self.resolution_text = Text(self.right, bg=COLORS["button"], fg=COLORS["text"],
                                    font=("微软雅黑", 9), wrap="word", height=15)
        self.resolution_text.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        res_scroll = Scrollbar(self.right, command=self.resolution_text.yview)
        res_scroll.grid(row=1, column=1, sticky="ns")
        self.resolution_text.config(yscrollcommand=res_scroll.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_text(self.resolution_text)

        # 信息显示区域（用于显示规则、牌库信息等）
        self.info_frame = Frame(self.right, bg=COLORS["panel_bg"], relief="solid", bd=1)
        self.info_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0), padx=5)
        self.info_frame.grid_rowconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=1)

        # 信息显示标题和关闭按钮
        self.info_header = Frame(self.info_frame, bg=COLORS["panel_bg"])
        self.info_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.info_title = create_label(self.info_header, "", 11, COLORS["warning"])
        self.info_title.pack(side="left")

        self.info_close_btn = create_button(self.info_header, "✕", 8, 1, COLORS["danger"],
                                           command=self._hide_info_panel)
        self.info_close_btn.pack(side="right")

        # 信息内容区域
        self.info_content = Text(self.info_frame, bg=COLORS["panel_bg"], fg=COLORS["text"],
                                 font=("微软雅黑", 9), wrap="word", height=10, state="disabled")
        self.info_content.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        info_scroll = Scrollbar(self.info_frame, command=self.info_content.yview)
        info_scroll.grid(row=1, column=1, sticky="ns")
        self.info_content.config(yscrollcommand=info_scroll.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_text(self.info_content)

        # 默认隐藏信息面板
        self.info_frame.grid_remove()

        # 底部按钮
        self.btn_bar = Frame(self, bg=COLORS["background"])
        self.btn_bar.place(relx=0, rely=1, relwidth=1, height=55, y=-55)

        # 使用grid布局：三列，中间列自动扩展
        self.btn_bar.grid_columnconfigure(0, weight=1)  # 左列
        self.btn_bar.grid_columnconfigure(1, weight=0)  # 中列（固定大小）
        self.btn_bar.grid_columnconfigure(2, weight=1)  # 右列

        # 左按钮：逃离战斗/结束战斗
        btn_text = "💰 结束战斗" if self.is_endless_mode else "🚪 逃离战斗"
        escape_btn = create_button(self.btn_bar, btn_text, 15, 2,
                                  COLORS["danger"], command=self._escape_battle)
        escape_btn.grid(row=0, column=0, padx=20, sticky="w")

        # 中按钮：确认出牌/开始结算（主要按钮）
        self.confirm_btn = create_button(self.btn_bar, "🎮 确认出牌", 20, 2,
                                         COLORS["success"], command=self._confirm_placement)
        self.confirm_btn.grid(row=0, column=1, padx=10)

        # 右按钮：查看牌库
        deck_btn = create_button(self.btn_bar, "🃏 查看牌库", 15, 2,
                                 COLORS["info"], command=self._show_decks)
        deck_btn.grid(row=0, column=2, padx=20, sticky="e")

    def _add_endless_info_display(self):
        """添加无尽模式实时信息显示"""
        # 创建信息显示框架
        info_frame = Frame(self.top, bg=COLORS["panel_bg"])
        info_frame.pack(side="left", padx=10, pady=5)

        # 初始显示
        self.endless_info_label = Label(info_frame,
            text="",
            font=("微软雅黑", 11), bg=COLORS["panel_bg"], fg=COLORS["warning"])
        self.endless_info_label.pack()

        # 立即更新一次显示
        self._update_endless_info()

    def _update_endless_info(self):
        """更新无尽模式信息显示"""
        if not self.is_endless_mode or not self.endless_info_label:
            return

        try:
            # 尝试从父级获取无尽模式状态
            win_streak = self._get_endless_streak()
            current_round = win_streak + 1  # 当前是第几场
            current_reward = 3 * (2 ** win_streak)  # 本场奖金：3 × 2^(n-1)

            self.endless_info_label.config(
                text=f"第{current_round}场 | 奖金:{current_reward} 💵"
            )

        except Exception as e:
            # 如果获取失败，显示默认信息，并稍后重试
            self.endless_info_label.config(
                text="无尽模式 | 加载中..."
            )
            # 100ms后重试
            self.after(100, self._update_endless_info)

    def _get_endless_streak(self):
        """获取无尽模式的连胜数"""
        # 方法1：直接检查父级是否有win_streak属性
        parent = self.master
        if hasattr(parent, 'win_streak'):
            return parent.win_streak

        # 方法2：查找父级的所有子组件，寻找EndlessMode实例
        for widget in parent.winfo_children():
            if hasattr(widget, '__class__') and widget.__class__.__name__ == 'EndlessMode':
                if hasattr(widget, 'win_streak'):
                    return widget.win_streak

        # 方法3：如果父级是Game类，查找其属性中的无尽模式实例
        if hasattr(parent, 'endless_mode') and parent.endless_mode:
            if hasattr(parent.endless_mode, 'win_streak'):
                return parent.endless_mode.win_streak

        # 如果都找不到，返回0
        return 0

    def _show_info_panel(self, title: str, content: str):
        """显示信息面板"""
        self.info_title.config(text=title)
        self.info_content.config(state="normal")
        self.info_content.delete("1.0", "end")
        self.info_content.insert("1.0", content)
        self.info_content.config(state="disabled")
        self.info_frame.grid()

    def _hide_info_panel(self):
        """隐藏信息面板"""
        self.info_frame.grid_remove()

    def _build_mid(self, mid):
        """中间区域：上 1/8 日志，下 7/8 出牌区+手牌"""
        # 日志区（压缩到1/8）
        log_frame = Frame(mid, bg=COLORS["background"])
        log_frame.place(relx=0, rely=0, relwidth=1, relheight=1/8)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = Text(log_frame, bg=COLORS["panel_bg"], fg=COLORS["text"],
                             font=("微软雅黑", 10), wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 绑定鼠标滚轮
        bind_mouse_wheel_to_text(self.log_text)

        # 战斗区
        battle = Frame(mid, bg=COLORS["background"])
        battle.place(relx=0, rely=1/8, relwidth=1, relheight=7/8)

        # 手牌区（贴底，加高到160px）
        hand_outer = Frame(battle, bg=COLORS["background"], bd=2, relief="ridge",
                           highlightbackground=COLORS["info_light"], highlightthickness=2)
        hand_outer.place(relx=0, rely=1, relwidth=1, height=160, y=-160)
        create_label(hand_outer, "🎴 你的手牌（点击选择）", 13, COLORS["info"]).pack(pady=(4, 2))
        self.hand_frame = Frame(hand_outer, bg=COLORS["background"])
        self.hand_frame.pack(fill="x", padx=10, pady=2)

        # 出牌区（撑满剩余空间）
        slots_area = Frame(battle, bg=COLORS["background"])
        slots_area.place(relx=0, rely=0, relwidth=1, relheight=1, height=-160)

        ai_area = Frame(slots_area, bg=COLORS["background"])
        ai_area.pack(expand=True, fill="both")
        create_label(ai_area, "🤖 电脑出牌区", 13, COLORS["warning"]).pack(expand=True)
        self.ai_slots = []
        ai_cards = Frame(ai_area, bg=COLORS["background"])
        ai_cards.pack(expand=True)
        for _ in range(5):
            cell = Frame(ai_cards, bg=COLORS["background"], width=80, height=110)
            cell.pack_propagate(False)
            cell.pack(side="left", padx=5)
            btn = create_button(cell, "🂠", 1, 1, COLORS["button"], command=lambda: None)
            btn.pack(fill="both", expand=True)
            self.ai_slots.append(btn)

        player_area = Frame(slots_area, bg=COLORS["background"])
        player_area.pack(expand=True, fill="both")
        create_label(player_area, "👤 你的出牌区（点击空位放置选中的牌）",
                     13, COLORS["success"]).pack(expand=True)
        self.player_slots = []
        player_cards = Frame(player_area, bg=COLORS["background"])
        player_cards.pack(expand=True)
        for i in range(5):
            cell = Frame(player_cards, bg=COLORS["background"], width=80, height=110)
            cell.pack_propagate(False)
            cell.pack(side="left", padx=5)
            btn = create_button(cell, "空位", 1, 1, COLORS["button"],
                                command=lambda i=i: self._on_slot_click(i))
            btn.pack(fill="both", expand=True)
            self.player_slots.append(btn)

    # ==================== 显示更新 ====================

    def _add_log(self, message):
        ts = time.strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_logs(self):
        for widget in (self.log_text, self.resolution_text):
            widget.config(state="normal")
            widget.delete(1.0, "end")
            widget.config(state="disabled")

    def _update_hp_display(self):
        self.p_hp_label.config(text=f"❤️ 玩家：{self.player.hp:.3f}")
        self.ai_hp_label.config(text=f"🤖 电脑：{self.ai.hp:.3f}")
        self.ai_hand_label.config(text=f"手牌：{len(self.ai.hand)}张")
        self.turn_label.config(text=f"第 {self.turn} 回合")

    def _update_slot_display(self):
        if not hasattr(self, "player_slots") or not self.player_slots:
            return
        for i, btn in enumerate(self.player_slots):
            card = self.player.slots[i]
            if card:
                img = _get_card_image(card.card_type)
                if img:
                    btn.config(text=f"{card.name}{card.number}", image=img,
                               compound="bottom", bg=card.color, fg="white")
                    btn.image = img
                else:
                    btn.config(text=f"{card.name}\n{card.number}", image="",
                               compound="none", bg=card.color, fg="white")
            else:
                btn.config(text="空位", image="", compound="none",
                           bg=COLORS["button"], fg="white")
        for i, btn in enumerate(self.ai_slots):
            card = self.ai.slots[i]
            if card:
                img = _get_card_image(card.card_type)
                if img:
                    btn.config(text=f"{card.name}{card.number}", image=img,
                               compound="bottom", bg=card.color, fg="white")
                    btn.image = img
                else:
                    btn.config(text=f"{card.name}\n{card.number}", image="",
                               compound="none", bg=card.color, fg="white")
            else:
                btn.config(text="🂠", image="", compound="none",
                           bg=COLORS["button"], fg="white")

    def _update_hand_display(self):
        for w in self.hand_frame.winfo_children():
            w.pack_forget()
        self.hand_buttons = []
        for card in self.player.hand[:10]:
            img = _get_card_image(card.card_type)
            if img:
                btn = Button(self.hand_frame,
                             text=f"{card.name}{card.number}", image=img,
                             compound="top", bg=card.color, fg="white",
                             width=56, height=100,
                             font=("Arial", 10, "bold"),
                             command=lambda c=card: self._on_hand_card_click(c))
                btn.image = img
            else:
                btn = Button(self.hand_frame,
                             text=f"{card.name}{card.number}",
                             bg=card.color, fg="white", width=5, height=3,
                             font=("Arial", 11, "bold"),
                             command=lambda c=card: self._on_hand_card_click(c))
            btn.pack(side="left", padx=3)
            self.hand_buttons.append(btn)
        if len(self.player.hand) > 10:
            Label(self.hand_frame, text=f"...等{len(self.player.hand)-10}张",
                  bg=COLORS["background"], fg=COLORS["text"]).pack(side="left", padx=5)

    def _refresh_attr_panel(self):
        """刷新左侧属性面板（显示双方属性）"""
        for w in self.attr_content_frame.winfo_children():
            w.destroy()

        def _section(label_text, label_color, player_obj, is_ai=False):
            # 如果是电脑，先显示强化次数
            if is_ai and self.ai_attrs:
                # 计算AI强化次数（统计非零属性的数量）
                reinforcement_count = self._calculate_ai_reinforcements()
                if reinforcement_count > 0:
                    Label(self.attr_content_frame,
                          text=f"💪 强化次数：{reinforcement_count}次",
                          bg=COLORS["panel_bg"],
                          fg=COLORS["warning"],
                          font=("微软雅黑", 11, "bold")).pack(anchor="w", pady=(2, 4))

            Label(self.attr_content_frame, text=label_text, bg=COLORS["panel_bg"],
                  fg=label_color, font=("微软雅黑", 11, "bold")).pack(anchor="w", pady=(6, 2))
            p = player_obj
            for text in [
                f"  最大HP: {p.max_hp:.1f}",
                f"  伤害加成: {p.damage_bonus*100:.0f}%",
                f"  暴击率: {p.crit_rate*100:.0f}%",
                f"  暴击额外伤害: {p.crit_damage*100:.0f}%",
                f"  吸血: {p.lifesteal*100:.0f}%",
                f"  免伤: {p.damage_reduction*100:.0f}%",
                f"  闪避: {p.dodge_chance*100:.0f}%",
            ]:
                Label(self.attr_content_frame, text=text, bg=COLORS["panel_bg"],
                      fg=COLORS["text"], font=("微软雅黑", 11)).pack(anchor="w", pady=1)

        _section("👤 玩家", COLORS["success"], self.player, is_ai=False)
        Frame(self.attr_content_frame, bg=COLORS["divider"], height=1).pack(fill="x", pady=4)
        _section("🤖 电脑", COLORS["danger"], self.ai, is_ai=True)

    def _calculate_ai_reinforcements(self):
        """计算AI强化次数（根据属性值与基础值的差异估算）"""
        if not self.ai_attrs:
            return 0

        # 根据属性值与基础值的差异估算强化次数
        # 每个奖励对应的增加值（参考tournament.py的_apply_ai_reward方法）
        reward_increments = {
            "max_hp": 1.0,           # 血量+1
            "damage_bonus": 0.1,     # 伤害加成+10%
            "crit_rate": 0.10,       # 暴击率+10%
            "crit_damage": 1.5,      # 暴击伤害+150%
            "lifesteal": 0.1,        # 吸血+10%
            "damage_reduction": 0.1, # 免伤+10%
            "dodge_chance": 0.05,    # 闪避+5%
        }

        # 基础属性值
        base_attrs = {
            "max_hp": 10.0,          # 基础最大HP
            "damage_bonus": 0.0,     # 基础伤害加成
            "crit_rate": 0.05,       # 基础暴击率
            "crit_damage": 0.5,      # 基础暴击伤害
            "lifesteal": 0.0,        # 基础吸血
            "damage_reduction": 0.0, # 基础免伤
            "dodge_chance": 0.0,     # 基础闪避
        }

        reinforcement_count = 0

        for attr_name, base_value in base_attrs.items():
            current_value = self.ai_attrs.get(attr_name, base_value)
            increment = reward_increments.get(attr_name, 0.01)  # 默认增量

            if current_value > base_value:
                # 计算大约获得了多少次该类型的强化
                # 使用四舍五入，考虑浮点数精度问题
                diff = current_value - base_value
                count = round(diff / increment)
                reinforcement_count += max(1, count)  # 至少计为1次

        return reinforcement_count

    # ==================== 交互逻辑 ====================

    def _on_hand_card_click(self, card):
        if self.phase == "place":
            self.selected_card = card
            self._add_log(f"选择了 {card.name}{card.number}")

    def _on_slot_click(self, slot_idx):
        if self.phase != "place":
            return
        existing = self.player.slots[slot_idx]
        if existing:
            self.player.hand.append(existing)
            self.player.slots[slot_idx] = None
            self._add_log(f"收回 {existing.name}{existing.number} 到手牌")
        elif self.selected_card:
            if self.player.place_card(self.selected_card, slot_idx):
                self._add_log(f"放置 {self.selected_card.name}{self.selected_card.number} 到位置{slot_idx+1}")
                self.selected_card = None
        self._update_slot_display()
        self._update_hand_display()

    def _confirm_placement(self):
        if sum(1 for c in self.player.slots if c) == 0:
            self._add_log("⚠️ 请至少放置一张牌！")
            return
        self.phase = "resolve"
        self._add_log("--- 确认出牌 ---")
        self._ai_place_cards()
        self._update_slot_display()
        self._update_hp_display()
        self.confirm_btn.config(text="⏭️ 开始结算", command=self._resolve_turn)

    def _ai_place_cards(self):
        self.ai.clear_slots()
        hand_count = len(self.ai.hand)
        if hand_count == 0:
            self._add_log("🤖 电脑无牌可出")
            return
        card_count = (min(hand_count, 5) if self.ai.hp < 4
                      else random.randint(max(1, int(hand_count * 0.4)), min(5, hand_count)))
        cards     = random.sample(self.ai.hand, card_count)
        positions = random.sample(range(5), card_count)
        for card, pos in zip(cards, positions):
            self.ai.hand.remove(card)
            self.ai.slots[pos] = card
        self._add_log(f"🤖 电脑出牌：{[f'{c.name}{c.number}' for c in cards]}")

    def _resolve_turn(self):
        self.confirm_btn.config(state="disabled", text="⏳ 结算中...")

        player_slots = self.player.slots.copy()
        ai_slots     = self.ai.slots.copy()
        steps = PositionBattleLogic.resolve_battle(
            self.player, self.ai, player_slots, ai_slots)

        self.resolution_text.config(state="normal")
        self.resolution_text.delete(1.0, "end")
        self.resolution_text.config(state="disabled")

        self._animate_steps(steps, 0)

    # 高亮颜色常量
    _HIGHLIGHT_COLOR  = COLORS["highlight"]   # 当前位置高亮（金色）
    _HIGHLIGHT_DELAY  = 1000         # 每个位置停留 ms
    _RESULT_DELAY     = 1000         # 显示结果后停留 ms

    def _animate_steps(self, steps, idx):
        """逐位置动画播放"""
        # 先恢复上一个位置的颜色
        self._restore_slot_colors()

        if idx >= len(steps):
            # 全部结算完毕
            self._update_hp_display()
            self._refresh_attr_panel()
            self._on_resolve_done()
            return

        step = steps[idx]
        pos  = step["pos"]

        # 高亮前从牌对象读颜色保存，供恢复使用
        p_card = self.player.slots[pos]
        a_card = self.ai.slots[pos]
        self._saved_colors = {
            "p": (pos, p_card.color if p_card else COLORS["button"]),
            "a": (pos, a_card.color if a_card else COLORS["button"]),
        }

        # 高亮当前位置的双方槽位
        self.player_slots[pos].config(bg=self._HIGHLIGHT_COLOR,
                                      fg="#000000" if p_card else COLORS["text"])
        self.ai_slots[pos].config(bg=self._HIGHLIGHT_COLOR,
                                  fg="#000000" if a_card else COLORS["text"])

        # 写入预生成日志
        logs_before = list(step["logs"])
        for log in logs_before:
            self._append_resolution(log)
            self._add_log(log)

        # 执行伤害动作（反击等动态日志会追加到 step["logs"]）
        for action in step["actions"]:
            action()

        # 补写 action 执行期间动态追加的日志
        for log in step["logs"][len(logs_before):]:
            self._append_resolution(log)
            self._add_log(log)

        # 更新 HP 显示（实时）
        self._update_hp_display()

        # 追加当前血量到结算日志
        self._append_resolution(
            f"  当前：玩家 {self.player.hp:.3f} ❤️  电脑 {self.ai.hp:.3f} ❤️"
        )

        # 有人死亡则立刻终止后续位置结算
        if self.player.is_dead() or self.ai.is_dead():
            self.after(self._RESULT_DELAY, self._on_resolve_done)
            return

        # 延迟后处理下一位置
        self.after(self._HIGHLIGHT_DELAY, lambda: self._animate_steps(steps, idx + 1))

    def _restore_slot_colors(self):
        """恢复所有槽位到正常颜色（直接重绘）"""
        self._update_slot_display()
        self._saved_colors = None

    def _append_resolution(self, text):
        self.resolution_text.config(state="normal")
        self.resolution_text.insert("end", text + "\n")
        self.resolution_text.see("end")
        self.resolution_text.config(state="disabled")

    def _on_resolve_done(self):
        """所有位置结算完毕后的后续处理"""
        self._restore_slot_colors()
        if self.player.is_dead() and self.ai.is_dead():
            self._add_log("⚖️ 双方同时阵亡！平局")
            self._game_over("平局")
        elif self.player.is_dead():
            self._add_log("💀 你被击败了！")
            self._game_over("lose")
        elif self.ai.is_dead():
            self._add_log("🎉 你赢了！")
            if self.is_final:
                self._show_champion_celebration()
            else:
                self._show_reward_selection()
        else:
            self._next_turn()

    def _next_turn(self):
        self.turn += 1
        self.phase = "place"
        self.player.clear_slots()
        self.ai.clear_slots()
        old_hand = len(self.player.hand)
        self.player.draw_cards()
        self.ai.draw_cards()
        self._add_log(f"--- 第 {self.turn} 回合开始 ---")
        self._add_log(f"抽牌 {len(self.player.hand) - old_hand} 张")
        self._update_hp_display()
        self._update_slot_display()
        self._update_hand_display()
        self.confirm_btn.config(state="normal", text="🎮 确认出牌",
                                command=self._confirm_placement)

    def _escape_battle(self):
        if self.is_endless_mode:
            # 无尽模式：结束战斗并结算
            if self.endless_mode_instance:
                # 从无尽模式实例获取状态
                win_streak = self.endless_mode_instance.win_streak
                pending_reward = self.endless_mode_instance.pending_reward
            else:
                # 回退：尝试从父级获取
                win_streak = getattr(self.master, 'win_streak', 0)
                pending_reward = getattr(self.master, 'pending_reward', 0)

            if messagebox.askyesno(
                "结束无尽战斗",
                f"确定要结束无尽战斗并结算奖金吗？\n\n"
                f"当前连胜：{win_streak}场\n"
                f"可获得奖金：{pending_reward}钞票\n\n"
                f"结束后将返回角色选择界面。"
            ):
                # 调用无尽模式的结束方法
                if self.endless_mode_instance and hasattr(self.endless_mode_instance, '_end_battle_early'):
                    self.endless_mode_instance._end_battle_early()
                elif hasattr(self.master, '_end_battle_early'):
                    self.master._end_battle_early()
        else:
            # 普通模式：逃离战斗
            if messagebox.askyesno("逃离战斗", "确定要逃离战斗并返回角色选择界面吗？\n（本局进度将不会保存）"):
                if self.on_lose:
                    self.on_lose()

    def _show_decks(self):
        """显示双方牌库信息（在信息面板中）"""

        def cards_str(cards):
            if not cards:
                return "  （空）"
            # 按牌名分组，每组一行，显示所有序号
            from collections import defaultdict
            groups = defaultdict(list)
            for c in sorted(cards, key=lambda x: (x.name, x.number)):
                groups[c.name].append(str(c.number))
            return "\n".join(f"  {name}：{', '.join(nums)}" for name, nums in groups.items())

        def section(player, player_name):
            lines = []
            lines.append(f"【{player_name}】")
            lines.append(f"── 牌库剩余 {len(player.deck.cards)} 张 ──")
            lines.append(cards_str(player.deck.cards))
            lines.append(f"── 弃牌堆 {len(player.deck.discard)} 张 ──")
            lines.append(cards_str(player.deck.discard))
            lines.append(f"── 手牌 {len(player.hand)} 张 ──")
            lines.append(cards_str(player.hand))
            slot_cards = [c for c in player.slots if c]
            lines.append(f"── 场上 {len(slot_cards)} 张 ──")
            lines.append(cards_str(slot_cards))
            lines.append(f"── 重洗次数：{player.deck.refill_count}/2 ──")
            return "\n".join(lines)

        # 生成牌库信息
        player_section = section(self.player, f"玩家 [{self.player.name}]")
        ai_section = section(self.ai, f"电脑 [{self.ai.name}]")

        content = f"{player_section}\n\n{ai_section}"
        self._show_info_panel("🃏 牌库信息", content)

    def _game_over(self, result):
        self.confirm_btn.config(state="disabled", text="💀 游戏结束")
        hand_buttons = self.hand_buttons if hasattr(self, "hand_buttons") else []
        for btn in self.player_slots + hand_buttons:
            btn.config(state="disabled")

        # 显示游戏结束界面
        self._show_game_over_screen(result)

    # ==================== 奖励 ====================

    def _show_reward_selection(self):
        # 移除战斗界面，显示奖励选择界面
        self._clear_battle_ui()

        # 创建奖励选择Frame
        self.reward_frame = Frame(self, bg=COLORS["background"])
        self.reward_frame.pack(fill="both", expand=True, padx=50, pady=50)

        # 标题
        title_label = Label(self.reward_frame, text="🎉 获胜奖励选择",
                           font=("Microsoft YaHei", 28, "bold"),
                           fg=COLORS["success"], bg=COLORS["background"])
        title_label.pack(pady=40)

        # 提示文字
        hint_label = Label(self.reward_frame, text="从以下三个强化属性中选择一个：",
                          font=("Microsoft YaHei", 14),
                          fg=COLORS["text_secondary"], bg=COLORS["background"])
        hint_label.pack(pady=(0, 30))

        # 奖励按钮容器
        button_frame = Frame(self.reward_frame, bg=COLORS["background"])
        button_frame.pack(pady=20)

        p = self.player
        all_rewards = [
            {"name": "吸血+10%",      "func": lambda: setattr(p, "lifesteal",        p.lifesteal + 0.1)},
            {"name": "免伤+10%",      "func": lambda: setattr(p, "damage_reduction", p.damage_reduction + 0.1)},
            {"name": "伤害+10%",      "func": lambda: setattr(p, "damage_bonus",     p.damage_bonus + 0.1)},
            {"name": "暴击率+10%",    "func": lambda: setattr(p, "crit_rate",        p.crit_rate + 0.10)},
            {"name": "暴击额外伤害+150%", "func": lambda: setattr(p, "crit_damage", p.crit_damage + 1.5)},
            {"name": "闪避+5%",       "func": lambda: setattr(p, "dodge_chance",     p.dodge_chance + 0.05)},
            {"name": "最大HP+1",      "func": self._reward_add_hp},
        ]

        # 随机选择3个奖励
        selected_rewards = random.sample(all_rewards, 3)

        # 创建奖励按钮
        for i, reward in enumerate(selected_rewards):
            btn = Button(button_frame, text=reward["name"],
                        font=("Microsoft YaHei", 16),
                        bg=COLORS["success"], fg="white",
                        width=30, height=2,
                        command=lambda r=reward: self._select_reward_switch(r))
            btn.pack(pady=15)

        # 添加边框
        border_frame = Frame(self.reward_frame, bg=COLORS["dark_purple"], bd=4, relief="solid")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=700, height=500)
        border_frame.lower()  # 放到背景层

    def _clear_battle_ui(self):
        """清除战斗界面元素"""
        # 清除所有战斗界面组件
        for widget in self.winfo_children():
            widget.destroy()

    def _reward_add_hp(self):
        self.player.max_hp += 1
        self.player.hp = min(self.player.hp + 1, self.player.max_hp)

    def _select_reward_switch(self, reward):
        """切换式奖励选择"""
        reward["func"]()

        # 保存属性并触发胜利回调
        attrs = self.save_player_attrs()
        if self.on_win:
            self.on_win(attrs)

    def _select_reward(self, reward, window):
        """旧版奖励选择（保留兼容性）"""
        reward["func"]()
        self._add_log(f"🎁 获得奖励：{reward['name']}")
        window.destroy()
        attrs = self.save_player_attrs()
        if self.on_win:
            self.on_win(attrs)

    def _show_champion_celebration(self):
        """显示冠军庆祝界面"""
        # 移除战斗界面
        self._clear_battle_ui()

        # 创建冠军庆祝Frame
        self.champion_frame = Frame(self, bg=COLORS["background"])
        self.champion_frame.pack(fill="both", expand=True, padx=50, pady=50)

        # 标题
        title_label = Label(self.champion_frame, text="🏆 总冠军！🏆",
                           font=("Microsoft YaHei", 36, "bold"),
                           fg=COLORS["highlight"], bg=COLORS["background"])
        title_label.pack(pady=40)

        # 庆祝文字
        congrats_label = Label(self.champion_frame, text="🎉 恭喜你获得罪恶巷口总冠军！\n你证明了自己是街头最强的斗士！",
                              font=("Microsoft YaHei", 18),
                              fg=COLORS["success"], bg=COLORS["background"])
        congrats_label.pack(pady=20)

        # 显示货币奖励信息
        from game.constants import DIFFICULTY_REWARDS, CURRENCY_SYMBOL
        reward_amount = DIFFICULTY_REWARDS.get(self.difficulty, 0)
        if reward_amount > 0:
            reward_label = Label(self.champion_frame,
                                text=f"💰 获得冠军奖励：{CURRENCY_SYMBOL} {reward_amount}",
                                font=("Microsoft YaHei", 16),
                                fg=COLORS["warning"], bg=COLORS["background"])
            reward_label.pack(pady=20)

        # 继续按钮
        continue_button = Button(self.champion_frame, text="返回锦标赛",
                                font=("Microsoft YaHei", 16, "bold"),
                                bg=COLORS["success"], fg="white",
                                width=20, height=2,
                                command=self._on_champion_continue)
        continue_button.pack(pady=40)

        # 添加边框
        border_frame = Frame(self.champion_frame, bg=COLORS["dark_purple"], bd=4, relief="solid")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=700, height=400)
        border_frame.lower()  # 放到背景层

    def _on_champion_continue(self):
        """冠军庆祝界面继续按钮回调"""
        # 保存属性并触发胜利回调
        attrs = self.save_player_attrs()
        if self.on_win:
            self.on_win(attrs)

    def _show_game_over_screen(self, result):
        """显示游戏结束界面"""
        # 移除战斗界面
        self._clear_battle_ui()

        # 创建游戏结束Frame
        self.game_over_frame = Frame(self, bg=COLORS["background"])
        self.game_over_frame.pack(fill="both", expand=True, padx=50, pady=50)

        # 根据结果设置不同的标题和消息
        if result == "lose":
            title_text = "💀 战斗结束"
            message_text = "你被击败了！"
            title_color = COLORS["danger"]
            message_color = COLORS["danger_light"]
        else:  # 平局
            title_text = "⚖️ 战斗结束"
            message_text = "平局！"
            title_color = COLORS["warning"]
            message_color = COLORS["warning_light"]

        # 标题
        title_label = Label(self.game_over_frame, text=title_text,
                           font=("Microsoft YaHei", 36, "bold"),
                           fg=title_color, bg=COLORS["background"])
        title_label.pack(pady=40)

        # 消息
        message_label = Label(self.game_over_frame, text=message_text,
                             font=("Microsoft YaHei", 20),
                             fg=message_color, bg=COLORS["background"])
        message_label.pack(pady=20)

        # 继续按钮
        continue_button = Button(self.game_over_frame, text="返回",
                                font=("Microsoft YaHei", 16, "bold"),
                                bg=COLORS["button"], fg="white",
                                width=20, height=2,
                                command=lambda: self._on_game_over_continue(result))
        continue_button.pack(pady=40)

        # 添加边框
        border_frame = Frame(self.game_over_frame, bg=COLORS["dark_purple"], bd=4, relief="solid")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=600, height=300)
        border_frame.lower()  # 放到背景层

    def _on_game_over_continue(self, result):
        """游戏结束界面继续按钮回调"""
        if result == "lose" or result == "平局":
            if self.on_lose:
                self.on_lose()

    # ==================== 规则弹窗 ====================

    def _show_rules(self):
        """显示游戏规则（在信息面板中）"""
        rules = (
            "━━━━━━━━  快速上手  ━━━━━━━━\n\n"
            "① 每回合把手牌放到 1~5 个位置\n"
            "② 点「确认出牌」→「开始结算」\n"
            "③ 双方按位置逐一对比，先偷牌再攻击\n"
            "④ 血量归零者失败\n\n"
            "卡牌类型：\n"
            "  🟥 拳  攻击用，数字越大越强\n"
            "  🟦 防  防御用，数字越大越难破\n"
            "  🟪 偷  复制对位的牌到手牌，原牌入弃牌堆\n\n"
            "━━━━━━━━  详细规则  ━━━━━━━━\n\n"
            "【拳 vs 拳】\n"
            "  数字大的一方先以 1.5 倍伤害出手\n"
            "  若对方未死，对方以 1.0 倍反击\n"
            "  数字相同：双方同时各出 1.0 倍\n\n"
            "【拳 vs 防】\n"
            "  拳数字 > 防数字：破防，造成 0.2 倍伤害\n"
            "  拳数字 ≤ 防数字：攻击被完全抵消\n\n"
            "【拳 vs 空位】\n"
            "  直接造成 1.0 倍伤害\n\n"
            "【偷牌】\n"
            "  偷走对位的牌，得到一张复制牌（名字带 '）\n"
            "  复制牌打出后不进弃牌堆，可被再次偷走\n"
            "  偷牌后本位置不再进行攻击\n\n"
            "【属性特效】\n"
            "  💥 暴击率  概率触发，伤害乘以（1 + 暴击额外伤害）\n"
            "  🛡️ 免伤    实际承受伤害 × (1 - 免伤)\n"
            "  🩸 吸血    造成伤害的一定比例回复生命\n"
            "  💨 闪避    概率完全躲避一次攻击\n\n"
            "【发牌规则】\n"
            "  每回合抽 4 张，手牌上限 = 当前HP × 2（最少 1）\n"
            "  牌库打完后最多重洗弃牌堆 2 次\n"
        )
        self._show_info_panel("📜 游戏规则", rules)

    # ==================== 属性存取 ====================

    def load_player_attrs(self, attrs):
        if not attrs:
            return
        for k, v in attrs.items():
            if hasattr(self.player, k):
                setattr(self.player, k, v)
        # 不重置HP为最大值，保持当前HP
        if hasattr(self, "p_hp_label"):
            self._update_hp_display()
            self._refresh_attr_panel()

    def save_player_attrs(self):
        """保存玩家属性（不包括装备加成）"""
        p = self.player

        # 获取当前装备属性
        inventory_manager = get_inventory_manager()
        equipment_attrs = inventory_manager.get_equipment_attributes()

        # 从当前属性中减去装备加成，得到基础属性+奖励加成
        saved_attrs = {}

        # 需要保存的属性列表
        attrs_to_save = [
            "damage_bonus", "lifesteal", "damage_reduction",
            "dodge_chance", "crit_rate", "crit_damage", "max_hp"
        ]

        # 获取角色基础属性
        cfg = self.character_config
        if not cfg:
            # 如果没有角色配置，使用默认角色
            from game.constants import CHARACTERS
            cfg = CHARACTERS.get("loulo", {})

        for attr_name in attrs_to_save:
            current_value = getattr(p, attr_name, 0)
            equipment_value = equipment_attrs.get(attr_name, 0)

            # 减去装备加成
            saved_value = current_value - equipment_value

            # 确保不会出现负值
            if attr_name == "max_hp":
                # max_hp至少为角色基础值
                base_hp = cfg.get("max_hp", 10)
                saved_value = max(saved_value, base_hp)
            elif saved_value < 0:
                saved_value = 0

            saved_attrs[attr_name] = saved_value

        return saved_attrs


# ==================== 独立测试入口 ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("卡牌对战 - 罪恶巷口")
    root.geometry("1200x800")
    CardBattle(root,
               on_win=lambda attrs: print("胜利！", attrs),
               on_lose=lambda: print("失败！")).pack(fill="both", expand=True)
    root.mainloop()
