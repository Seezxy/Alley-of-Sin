"""
开发者面板 — 游戏内调试工具
仅当 data/.dev_mode 存在或 GAME_DEV_MODE=1 时可用
"""
import tkinter as tk
from tkinter import Frame, Label, Entry, Button, Toplevel, messagebox
from game.attribute_utils import get_attribute_utils
from game.constants import COLORS

# 7 项战斗属性：属性名 → (显示名, 是否百分比)
_ATTR_DEFS = [
    ("max_hp",           "最大生命值",   False),
    ("damage_bonus",     "伤害加成",     True),
    ("crit_rate",        "暴击率",       True),
    ("crit_damage",      "暴击伤害",     True),
    ("lifesteal",        "生命偷取",     True),
    ("damage_reduction", "伤害减免",     True),
    ("dodge_chance",     "闪避几率",     True),
]


def _to_display(attr_name: str, value: float) -> str:
    """内部存储值 → 显示值"""
    if value is None:
        return "0"
    if attr_name == "max_hp":
        return str(int(value))
    return str(round(value * 100, 1))


def _from_display(attr_name: str, text: str) -> float:
    """显示值 → 内部存储值"""
    val = float(text or "0")
    if attr_name == "max_hp":
        return val
    return val / 100.0


class DevPanel:
    """开发者面板 — Toplevel 弹出窗口"""

    def __init__(self, parent, game):
        self._game = game
        self._user_manager = game.user_manager

        self._win = Toplevel(parent)
        self._win.title("开发者面板")
        self._win.resizable(False, False)
        self._win.configure(bg=COLORS["background"])
        self._win.transient(parent)
        self._win.grab_set()

        self._attr_entries = {}
        self._build_ui()
        self._center_window()

    def _center_window(self):
        self._win.update_idletasks()
        pw, ph = self._win.winfo_width(), self._win.winfo_height()
        sw, sh = self._win.winfo_screenwidth(), self._win.winfo_screenheight()
        x, y = (sw - pw) // 2, (sh - ph) // 2
        self._win.geometry(f"+{x}+{y}")

    # ── UI 构建 ──────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}

        # ── 货币区 ──
        cur_frame = Frame(self._win, bg=COLORS["background"])
        cur_frame.pack(fill="x", **pad)
        Label(cur_frame, text="💵 货币:", font=("Microsoft YaHei", 12),
              fg=COLORS["text"], bg=COLORS["background"]).pack(side="left")
        self._currency_var = tk.StringVar(value=str(self._user_manager.get_currency()))
        self._currency_entry = Entry(cur_frame, textvariable=self._currency_var,
                                     font=("Microsoft YaHei", 12), width=10)
        self._currency_entry.pack(side="left", padx=8)
        Button(cur_frame, text="修改", font=("Microsoft YaHei", 10),
               bg=COLORS["success"], fg="white", command=self._on_set_currency).pack(side="left")

        # ── 属性区 ──
        attr_label = Label(self._win, text="战斗属性（百分比输入如 5=5%）",
                           font=("Microsoft YaHei", 10, "italic"),
                           fg=COLORS.get("text_secondary", "#999"),
                           bg=COLORS["background"])
        attr_label.pack(anchor="w", padx=10, pady=(12, 0))

        attr_frame = Frame(self._win, bg=COLORS["background"])
        attr_frame.pack(fill="x", **pad)

        current_attrs = self._game.dev_player_attrs or {}
        for i, (attr_name, display_name, is_pct) in enumerate(_ATTR_DEFS):
            Label(attr_frame, text=display_name + ":", font=("Microsoft YaHei", 11),
                  fg=COLORS["text"], bg=COLORS["background"]).grid(
                  row=i, column=0, sticky="e", padx=(0, 6), pady=2)
            init_val = _to_display(attr_name, current_attrs.get(attr_name, 0))
            var = tk.StringVar(value=init_val)
            entry = Entry(attr_frame, textvariable=var,
                          font=("Microsoft YaHei", 11), width=8)
            entry.grid(row=i, column=1, pady=2)
            self._attr_entries[attr_name] = var
            if is_pct:
                Label(attr_frame, text="%", font=("Microsoft YaHei", 11),
                      fg=COLORS["text"], bg=COLORS["background"]).grid(
                      row=i, column=2, sticky="w", padx=(4, 0))

        # Save button for attrs
        Button(self._win, text="保存属性", font=("Microsoft YaHei", 12),
               bg=COLORS["highlight"], fg="white",
               command=self._on_save_attrs).pack(pady=(10, 4))

        # ── 快捷操作 ──
        sep = Frame(self._win, height=1, bg=COLORS["border"])
        sep.pack(fill="x", padx=10, pady=8)

        Button(btn_frame := Frame(self._win, bg=COLORS["background"]), text="重置属性",
               font=("Microsoft YaHei", 10), bg=COLORS["button"], fg=COLORS["text"],
               command=self._on_reset_attrs).pack(pady=(0, 10))
        btn_frame.pack(fill="x", padx=10)

    # ── 回调 ─────────────────────────────────────

    def _on_set_currency(self):
        try:
            amount = int(self._currency_var.get())
        except ValueError:
            messagebox.showwarning("无效输入", "货币必须是整数")
            return
        self._user_manager.set_currency(amount)
        self._currency_var.set(str(self._user_manager.get_currency()))

    def _on_save_attrs(self):
        attrs = {}
        for attr_name, _, _ in _ATTR_DEFS:
            text = self._attr_entries[attr_name].get()
            try:
                val = _from_display(attr_name, text)
            except ValueError:
                continue
            attrs[attr_name] = val
        # 应用边界检查
        au = get_attribute_utils()
        attrs = au.validate_and_fix_attributes(attrs)
        self._game.dev_player_attrs = attrs
        # 回写修正后的值到输入框
        for attr_name, var in self._attr_entries.items():
            var.set(_to_display(attr_name, attrs.get(attr_name, 0)))
        self._show_success("属性已保存")

    def _on_reset_attrs(self):
        self._game.dev_player_attrs = None
        for attr_name, var in self._attr_entries.items():
            var.set("0")
        self._show_success("属性已重置")

    def _show_success(self, msg):
        # 短暂显示绿色提示
        lbl = Label(self._win, text=msg, font=("Microsoft YaHei", 10),
                    fg="#4CAF50", bg=COLORS["background"])
        lbl.pack(pady=(2, 6))
        self._win.after(1500, lbl.destroy)
