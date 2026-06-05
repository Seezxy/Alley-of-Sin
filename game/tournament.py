"""
锦标赛界面
"""

from tkinter import Frame, messagebox
import random
from game.constants import COLORS, STAGES, CHARACTERS
from game.utils import create_button, create_header_label, create_label
from game.card_battle import CardBattle
from game.background_fill import fill_background_with_image


class Tournament(Frame):
    """锦标赛"""

    def __init__(self, root, on_back, on_lose_back):
        super().__init__(root, bg=COLORS["background"])
        self.on_back = on_back
        self.on_lose_back = on_lose_back
        self.current_stage = 0
        self.selected_character = None
        self.saved_player_attrs = None
        self.saved_ai_attrs = {}
        self.ai_rewards_per_stage = 1  # 默认标准难度
        self.card_battle = None
        self.widgets = []
        self._canvas = None
        self._setup_ui()

    def _clear_widgets(self):
        """清空所有组件"""
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []

    def _setup_ui(self):
        """设置界面"""
        from tkinter import Frame, Label
        self._clear_widgets()

        # 添加背景图片
        if not self._canvas:
            self._canvas = fill_background_with_image(
                self, "bg_menu.jpeg", "#404040"  # 中灰色，避免黑色闪烁
            )

        is_champion = self.current_stage == len(STAGES) - 1
        stage_text  = "🏆 总冠军！🏆" if is_champion else f"锦标赛 - {STAGES[self.current_stage]}"

        # 进度条：显示当前在哪一阶段
        progress_frame = Frame(self, bg=COLORS["background"])
        progress_frame.pack(pady=(30, 0))
        self.widgets.append(progress_frame)
        for i, stage in enumerate(STAGES[:-1]):  # 不显示"冠军"占位
            is_done    = i < self.current_stage
            is_current = i == self.current_stage
            color = COLORS["success"] if is_done else (COLORS["warning"] if is_current else COLORS["text_muted"])
            prefix = "✅ " if is_done else ("▶ " if is_current else "  ")
            Label(progress_frame, text=f"{prefix}{stage}",
                  bg=COLORS["background"], fg=color,
                  font=("微软雅黑", 11)).pack(side="left", padx=8)

        # 标题
        stage_label = create_header_label(self, stage_text, font_size=36)
        stage_label.pack(pady=(20, 10))
        self.widgets.append(stage_label)

        # 角色属性卡片
        char_key = self.selected_character or "loulo"
        char_cfg = CHARACTERS[char_key]
        attrs    = self.saved_player_attrs or {}

        # 获取装备属性
        from game.inventory import get_inventory_manager
        inventory_manager = get_inventory_manager()
        equipment_attrs = inventory_manager.get_equipment_attributes()

        # 基础属性（保存的属性或角色基础属性）
        base_max_hp           = attrs.get("max_hp",           char_cfg["max_hp"])
        base_damage_bonus     = attrs.get("damage_bonus",     char_cfg["damage_bonus"])
        base_crit_rate        = attrs.get("crit_rate",        char_cfg["crit_rate"])
        base_crit_damage      = attrs.get("crit_damage",      char_cfg["crit_damage"])
        base_lifesteal        = attrs.get("lifesteal",        char_cfg["lifesteal"])
        base_damage_reduction = attrs.get("damage_reduction", char_cfg["damage_reduction"])
        base_dodge_chance     = attrs.get("dodge_chance",     char_cfg["dodge_chance"])

        # 最终属性（基础属性 + 装备属性）
        max_hp           = base_max_hp + equipment_attrs.get('max_hp', 0)
        damage_bonus     = base_damage_bonus + equipment_attrs.get('damage_bonus', 0)
        crit_rate        = base_crit_rate + equipment_attrs.get('crit_rate', 0)
        crit_damage      = base_crit_damage + equipment_attrs.get('crit_damage', 0)
        lifesteal        = base_lifesteal + equipment_attrs.get('lifesteal', 0)
        damage_reduction = base_damage_reduction + equipment_attrs.get('damage_reduction', 0)
        dodge_chance     = base_dodge_chance + equipment_attrs.get('dodge_chance', 0)

        card = Frame(self, bg=COLORS["card_bg"], relief="solid", bd=1)
        card.pack(pady=10, padx=60, fill="x")
        self.widgets.append(card)

        # 卡片标题 - 显示角色名称和是否包含装备加成
        if equipment_attrs:
            title_text = f"🎭 {char_cfg['name']}  ·  🎯 装备加成后属性"
            title_color = COLORS["highlight"]
        else:
            title_text = f"🎭 {char_cfg['name']}  ·  {char_cfg['desc']}"
            title_color = COLORS["warning"]

        Label(card, text=title_text,
              bg=COLORS["card_bg"], fg=title_color,
              font=("微软雅黑", 14, "bold")).pack(pady=(12, 6))

        row = Frame(card, bg=COLORS["card_bg"])
        row.pack(pady=(0, 12), padx=20)

        stats = [
            ("❤️ 最大HP",    f"{max_hp:.1f}"),
            ("⚔️ 伤害加成",  f"{damage_bonus*100:.0f}%"),
            ("💥 暴击率",    f"{crit_rate*100:.0f}%"),
            ("🔥 暴击额外伤害",  f"{crit_damage*100:.0f}%"),
            ("🩸 吸血",      f"{lifesteal*100:.0f}%"),
            ("🛡️ 免伤",      f"{damage_reduction*100:.0f}%"),
            ("💨 闪避",      f"{dodge_chance*100:.0f}%"),
        ]
        for label, value in stats:
            col = Frame(row, bg=COLORS["button"], relief="flat", bd=0)
            col.pack(side="left", padx=6, pady=4, ipadx=10, ipady=6)
            Label(col, text=label, bg=COLORS["button"], fg=COLORS["text_secondary"],
                  font=("微软雅黑", 10)).pack()
            Label(col, text=value, bg=COLORS["button"], fg=COLORS["text"],
                  font=("微软雅黑", 13, "bold")).pack()

        # 冠军 / 战斗按钮
        if is_champion:
            congrats = create_label(
                self,
                "🎉 恭喜你获得罪恶巷口总冠军！\n你证明了自己是街头最强的斗士！",
                font_size=18, fg=COLORS["warning"]
            )
            congrats.pack(pady=30)
            self.widgets.append(congrats)
        else:
            battle_btn = create_button(
                self, "⚔️ 开始对战", width=20, height=3,
                bg=COLORS["success"], command=self._start_battle
            )
            battle_btn.pack(pady=25)
            self.widgets.append(battle_btn)

            hint = create_label(
                self,
                "通过卡牌对战决定胜负　　拳（攻）→ 防（守）→ 偷（技能）",
                font_size=12, fg=COLORS["warning"]
            )
            hint.pack(pady=4)
            self.widgets.append(hint)

        back_btn = create_button(self, "返回", width=15, height=2, command=self._on_back_click)
        back_btn.pack(pady=15)
        self.widgets.append(back_btn)

    def _start_battle(self):
        """开始卡牌对战"""
        self._clear_widgets()

        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None

        # 直接传入角色和已保存属性，跳过角色选择弹窗
        char_key = self.selected_character or "loulo"
        is_final = self.current_stage == len(STAGES) - 2
        self.card_battle = CardBattle(
            self,
            on_win=self._on_battle_win,
            on_lose=self._on_battle_lose,
            character_key=char_key,
            initial_attrs=self.saved_player_attrs,
            is_final=is_final,
            ai_attrs=self.saved_ai_attrs,
            difficulty=self.ai_rewards_per_stage
        )
        self.card_battle.pack(expand=True, fill="both", padx=20, pady=20)
        self.widgets.append(self.card_battle)

    def _exit_battle(self):
        """退出战斗"""
        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None
        self._setup_ui()

    # 修改：接收胜利后保存的属性
    def _on_battle_win(self, saved_attrs=None):
        """战斗胜利（奖励选择完成后触发）"""
        if saved_attrs:
            self.saved_player_attrs = saved_attrs

        # AI 随机获得一个奖励，为下一场积累
        self._apply_ai_reward()

        # 检查是否是冠军赛（赢得冠军）
        from game.constants import STAGES, DIFFICULTY_REWARDS
        is_champion = self.current_stage == len(STAGES) - 2  # 决赛胜利后成为冠军

        if is_champion:
            # 给予货币奖励
            reward_amount = DIFFICULTY_REWARDS.get(self.ai_rewards_per_stage, 0)
            if reward_amount > 0:
                from game.user_manager import get_user_manager
                user_manager = get_user_manager()
                user_manager.add_currency(reward_amount)
                # 货币奖励信息已经在冠军庆祝界面显示，不再弹出窗口

        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None
        self.current_stage += 1
        self._setup_ui()

    def _apply_ai_reward(self):
        """按难度给 AI 随机应用奖励（可重复）"""
        a = self.saved_ai_attrs
        rewards = [
            lambda: a.update({"lifesteal":        a.get("lifesteal", 0.0)        + 0.1}),
            lambda: a.update({"damage_reduction": a.get("damage_reduction", 0.0) + 0.1}),
            lambda: a.update({"damage_bonus":     a.get("damage_bonus", 0.0)     + 0.1}),
            lambda: a.update({"crit_rate":        a.get("crit_rate", 0.05)       + 0.10}),
            lambda: a.update({"crit_damage":      a.get("crit_damage", 0.5)      + 1.5}),
            lambda: a.update({"dodge_chance":     a.get("dodge_chance", 0.0)     + 0.05}),
            lambda: a.update({"max_hp":           a.get("max_hp", 10)            + 1}),
        ]
        for _ in range(self.ai_rewards_per_stage):
            random.choice(rewards)()

    def _on_battle_lose(self):
        """战斗失败"""
        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None
        # 无论当前阶段是什么，都返回角色选择界面
        self.on_back()

    def _on_back_click(self):
        """返回按钮点击，需要确认"""
        if messagebox.askyesno("确认返回", "确定要返回吗？当前锦标赛进度将不会保存。"):
            self.on_back()

    def on_win(self):
        """对战胜利 - 晋级"""
        self.current_stage += 1
        self._setup_ui()

    def on_lose(self):
        """对战失败 - 退回"""
        if self.current_stage > 0:
            self.current_stage -= 1
            self._setup_ui()
        else:
            self.on_lose_back()

    # 新增：重置锦标赛，支持传入保存的属性
    def show(self):
        """显示锦标赛 - 重置为 64 强"""
        self.current_stage = 0
        # 新增：重置时清空属性（首次开始锦标赛不继承之前的属性）
        self.saved_player_attrs = None
        self._setup_ui()

    # 新增：外部调用的重置方法（供 Game 类调用）
    def reset(self, saved_attrs=None, char_key="loulo", difficulty=1):
        """重置锦标赛，可传入保存的属性和难度"""
        self.current_stage        = 0
        self.saved_player_attrs   = saved_attrs
        self.saved_ai_attrs       = {}
        self.selected_character   = char_key
        self.ai_rewards_per_stage = difficulty
        self._setup_ui()
