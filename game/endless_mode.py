"""
无尽模式界面
"""

from tkinter import Frame, Label, messagebox
import random
from game.constants import COLORS, CHARACTERS, ENDLESS_MODE_CONFIG
from game.utils import create_button, create_header_label, create_label
from game.card_battle import CardBattle
from game.background_fill import fill_background_with_image
from game.user_manager import get_user_manager


class EndlessMode(Frame):
    """无尽模式"""

    def __init__(self, root, on_back, on_lose_back):
        super().__init__(root, bg=COLORS["background"])
        self.on_back = on_back
        self.on_lose_back = on_lose_back

        # 无尽模式状态
        self.win_streak = 0           # 当前连胜数
        self.pending_reward = 0       # 待结算奖金（当前连胜的总奖金）
        self.total_earned = 0         # 本次无尽模式已结算的总奖金
        self.ai_attrs = {}            # AI属性（累积强化）
        self.saved_player_attrs = None  # 玩家属性
        self.selected_character = None  # 当前角色
        self.difficulty = 3           # 固定为地狱难度
        self.damage_reduction_count = 0  # 免伤强化次数（达到10次后排除）

        self.card_battle = None
        self.widgets = []
        self._canvas = None

        # 界面组件
        self.streak_label = None
        self.current_reward_label = None
        self.total_reward_label = None

        self._setup_ui()

    def _calculate_win_reward(self, win_streak):
        """计算第n场胜利奖金：3 × 2^(n-1)（基础奖金3）"""
        if win_streak <= 0:
            return 0
        return 3 * (2 ** (win_streak - 1))

    def _calculate_total_reward(self, win_streak):
        """计算前n场胜利总奖金：3 × (2^n - 1)"""
        if win_streak <= 0:
            return 0
        return 3 * (2 ** win_streak - 1)

    def _apply_ai_reward(self):
        """按地狱难度给 AI 应用累积奖励（赢n场抽3n项，只限制免伤上限）"""
        # 可强化的属性列表
        attributes = [
            "lifesteal",
            "damage_reduction",
            "damage_bonus",
            "crit_rate",
            "crit_damage",
            "dodge_chance",
            "max_hp"
        ]

        # 如果免伤已经达到上限（0.99），从属性列表中排除免伤
        available_attributes = attributes.copy()
        if self.damage_reduction_count >= 10:  # 0.1×10=1.0，但上限0.99
            if "damage_reduction" in available_attributes:
                available_attributes.remove("damage_reduction")

        # 如果可用属性不足，使用所有属性
        if len(available_attributes) < self.difficulty:
            available_attributes = attributes.copy()

        # 本次胜利抽取3项强化（地狱难度每场3项）
        for _ in range(self.difficulty):
            # 随机选择一项属性强化
            attr = random.choice(available_attributes)

            # 应用强化
            if attr == "lifesteal":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.0) + 0.1
            elif attr == "damage_reduction":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.0) + 0.1
                self.damage_reduction_count += 1
            elif attr == "damage_bonus":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.0) + 0.1
            elif attr == "crit_rate":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.05) + 0.10
            elif attr == "crit_damage":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.5) + 1.5
            elif attr == "dodge_chance":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 0.0) + 0.05
            elif attr == "max_hp":
                self.ai_attrs[attr] = self.ai_attrs.get(attr, 10) + 1

        # 只限制免伤上限为0.99
        if "damage_reduction" in self.ai_attrs:
            if self.ai_attrs["damage_reduction"] > ENDLESS_MODE_CONFIG["max_damage_reduction"]:
                self.ai_attrs["damage_reduction"] = ENDLESS_MODE_CONFIG["max_damage_reduction"]

    def _clear_widgets(self):
        """清空所有组件"""
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []

    def _setup_ui(self):
        """设置无尽模式界面"""
        self._clear_widgets()

        # 添加背景图片
        if not self._canvas:
            self._canvas = fill_background_with_image(
                self, "bg_menu.jpeg", "#404040"  # 中灰色，避免黑色闪烁
            )

        # 标题
        title = create_header_label(self, "无尽模式", font_size=36)
        title.pack(pady=(50, 30))
        self.widgets.append(title)

        # 顶部信息栏：实时显示状态
        info_frame = Frame(self, bg=COLORS["panel_bg"])
        info_frame.pack(fill="x", padx=40, pady=10)
        self.widgets.append(info_frame)

        # 连胜显示
        self.streak_label = Label(info_frame,
            text=f"当前连胜：{self.win_streak}场",
            font=("微软雅黑", 14), bg=COLORS["panel_bg"], fg=COLORS["warning"])
        self.streak_label.pack(side="left", padx=20)

        # 本场奖金显示
        next_reward = self._calculate_win_reward(self.win_streak + 1)
        self.current_reward_label = Label(info_frame,
            text=f"本场奖金：{next_reward} 💵",
            font=("微软雅黑", 14), bg=COLORS["panel_bg"], fg=COLORS["success"])
        self.current_reward_label.pack(side="left", padx=20)

        # 累计奖金显示
        self.total_reward_label = Label(info_frame,
            text=f"累计奖金：{self.pending_reward} 💵",
            font=("微软雅黑", 14), bg=COLORS["panel_bg"], fg=COLORS["info"])
        self.total_reward_label.pack(side="left", padx=20)

        # 角色信息显示
        if self.selected_character:
            char_cfg = CHARACTERS[self.selected_character]
            char_label = Label(info_frame,
                text=f"角色：{char_cfg['name']}",
                font=("微软雅黑", 12), bg=COLORS["panel_bg"], fg=COLORS["text"])
            char_label.pack(side="right", padx=20)

        # 角色属性卡片（与其他难度看齐）
        if self.selected_character:
            char_cfg = CHARACTERS[self.selected_character]
            attrs = self.saved_player_attrs or {}

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
            card.pack(pady=20, padx=60, fill="x")
            self.widgets.append(card)

            # 卡片标题
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

        # 战斗按钮
        battle_text = "⚔️ 开始战斗" if self.win_streak == 0 else "⚔️ 继续战斗"
        battle_btn = create_button(self, battle_text, width=20, height=3,
                                  command=self._start_battle)
        battle_btn.pack(pady=20)
        self.widgets.append(battle_btn)

        # 结束战斗按钮
        end_btn = create_button(self, "💰 结束战斗并结算", width=20, height=2,
                               bg=COLORS["danger"], command=self._end_battle_early)
        end_btn.pack(pady=10)
        self.widgets.append(end_btn)

        # 无尽模式不显示返回按钮（用户只能通过"结束战斗并结算"退出）
        # 无尽模式不显示背包按钮（在无尽模式中禁用背包功能）

    def _update_display(self):
        """更新界面显示"""
        if self.streak_label:
            self.streak_label.config(text=f"当前连胜：{self.win_streak}场")

        if self.current_reward_label:
            next_reward = self._calculate_win_reward(self.win_streak + 1)
            self.current_reward_label.config(text=f"本场奖金：{next_reward} 💵")

        if self.total_reward_label:
            self.total_reward_label.config(text=f"累计奖金：{self.pending_reward} 💵")

    def _start_battle(self):
        """开始无尽战斗"""
        if not self.selected_character:
            messagebox.showerror("错误", "未选择角色")
            return

        # 创建战斗界面
        self.card_battle = CardBattle(
            self.master,
            on_win=self._on_battle_win,
            on_lose=self._on_battle_lose,
            character_key=self.selected_character,
            initial_attrs=self.saved_player_attrs,
            ai_attrs=self.ai_attrs,
            difficulty=self.difficulty,
            is_endless_mode=True,  # 标记为无尽模式
            endless_mode_instance=self  # 传递无尽模式实例
        )

        # 显示战斗界面
        self.card_battle.pack(expand=True, fill="both")
        self.pack_forget()

    def _on_battle_win(self, saved_attrs=None):
        """战斗胜利（奖励选择完成后触发）"""
        if saved_attrs:
            self.saved_player_attrs = saved_attrs

        # 增加连胜数
        self.win_streak += 1

        # 计算本场奖金并更新累计奖金
        self.pending_reward = self._calculate_total_reward(self.win_streak)

        # AI获得强化
        self._apply_ai_reward()

        # 销毁战斗界面
        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None

        # 更新显示并重新显示无尽模式界面
        self._update_display()
        self.pack(expand=True, fill="both")

        # 不显示胜利信息弹窗，与其他难度保持一致
        # 玩家可以在无尽模式界面看到更新的状态信息

    def _on_battle_lose(self):
        """战斗失败 - 结算奖金"""
        # 计算总奖金（所有连胜场次的总和）
        total_reward = self.pending_reward

        # 发放奖金
        if total_reward > 0:
            user_manager = get_user_manager()
            user_manager.add_currency(total_reward)
            self.total_earned += total_reward

        # 销毁战斗界面
        if self.card_battle:
            self.card_battle.destroy()
            self.card_battle = None

        # 显示结算信息
        self._show_settlement_screen(total_reward, early_exit=False)

        # 重置状态
        self._reset_state()

        # 返回角色选择
        self.on_back()

    def _end_battle_early(self):
        """提前结束战斗（玩家主动结束）"""
        # 计算当前累计奖金
        total_reward = self.pending_reward

        if total_reward == 0:
            # 没有连胜，直接返回
            if messagebox.askyesno("结束无尽战斗", "当前没有连胜记录，确定要结束吗？"):
                # 显示简单提示
                messagebox.showinfo("结束无尽战斗", "已结束无尽模式，返回角色选择界面。")
                self._reset_state()
                self.on_back()
            return

        # 确认对话框
        if messagebox.askyesno(
            "结束无尽战斗",
            f"确定要结束无尽战斗吗？\n\n"
            f"当前连胜：{self.win_streak}场\n"
            f"可获得奖金：{total_reward}钞票\n\n"
            f"结束后将返回角色选择界面。"
        ):
            # 发放奖金
            user_manager = get_user_manager()
            user_manager.add_currency(total_reward)
            self.total_earned += total_reward

            # 显示结算信息（在返回前显示）
            self._show_settlement_screen(total_reward, early_exit=True)

            # 重置状态
            self._reset_state()

            # 返回角色选择
            self.on_back()

    def _show_settlement_screen(self, total_reward, early_exit=False):
        """显示结算界面"""
        title = "无尽模式结算（主动结束）" if early_exit else "无尽模式结算（战斗失败）"
        message = f"{title}\n\n"
        message += f"连胜场次：{self.win_streak}场\n"
        message += f"获得奖金：{total_reward} 💵\n"

        if early_exit:
            message += "\n已主动结束无尽模式，奖金已发放到账户。"
        else:
            message += "\n战斗失败，连胜终止，奖金已发放到账户。"

        messagebox.showinfo("结算完成", message)

    def _reset_state(self):
        """重置无尽模式状态"""
        self.win_streak = 0
        self.pending_reward = 0
        self.ai_attrs = {}
        self.saved_player_attrs = None
        self.damage_reduction_count = 0

    def reset(self, saved_attrs=None, char_key="loulo"):
        """重置无尽模式"""
        self._reset_state()
        self.saved_player_attrs = saved_attrs
        self.selected_character = char_key
        self._setup_ui()

    def _add_inventory_button(self):
        """在左下角添加背包按钮"""
        inventory_button = create_button(
            self, "背包", width=10, height=2,
            command=self._on_inventory
        )
        # 放置在左下角
        inventory_button.place(relx=0.02, rely=0.95, anchor="sw")
        self.widgets.append(inventory_button)

    def _on_inventory(self):
        """打开背包界面"""
        # 这里需要从父级获取背包回调
        # 暂时使用简单实现
        try:
            from game.item_ui import InventoryWindow
            inventory_window = InventoryWindow(self.master)
            inventory_window.grab_set()  # 模态窗口
        except ImportError:
            messagebox.showinfo("背包", "背包功能暂不可用")