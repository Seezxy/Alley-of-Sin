"""
游戏数据模型
包含：Card, Deck, Player, DamageContext, PositionBattleLogic
"""

import random
from game.constants import COLORS, CHARACTERS, DEFAULT_DECK
from game.attribute_utils import get_attribute_utils

# ==================== 卡牌常量 ====================
CARD_TYPES = {
    "fist":   {"name": "拳", "color": "#E74C3C", "count": 30},
    "elbow":  {"name": "肘", "color": "#C0392B", "count": 10,
               "crit_rate_bonus": 0.5, "crit_damage_bonus": 1.0},  # 额外暴击率+50%，暴击额外伤害+100%
    "defend": {"name": "防", "color": "#3498DB", "count": 20},
    "steal":  {"name": "偷", "color": "#9B59B6", "count": 10},
}

INITIAL_HP    = 10
INITIAL_HAND  = 6
DRAW_PER_TURN = 4
BASE_ATTACK   = 1


# ==================== 卡牌 ====================
class Card:
    def __init__(self, card_type, number, is_copy=False):
        self.card_type        = card_type
        self.number           = number
        self.is_copy          = is_copy
        info                  = CARD_TYPES[card_type]
        self.name             = info["name"] + ("'" if is_copy else "")
        self.color            = info["color"]
        # 牌自带的暴击加成（肘牌专用，其他牌为0）
        self.crit_rate_bonus   = info.get("crit_rate_bonus", 0.0)
        self.crit_damage_bonus = info.get("crit_damage_bonus", 0.0)

    def make_copy(self):
        """返回一张复制牌（标记 is_copy=True，名字带'）"""
        c = Card(self.card_type, self.number, is_copy=True)
        return c


# ==================== 牌库 ====================
class Deck:
    """支持自定义牌库配置，最多重洗2次"""

    def __init__(self, deck_config=None):
        self.deck_config  = deck_config
        self.cards        = []
        self.discard      = []
        self.refill_count = 0
        self._build_deck()

    def _build_deck(self):
        self.cards = []
        config = self.deck_config or DEFAULT_DECK
        for card_type, count in config.items():
            for i in range(1, count + 1):
                number = i * 2 if card_type == "elbow" else i
                self.cards.append(Card(card_type, number))
        random.shuffle(self.cards)

    def draw(self, count=1):
        drawn = []
        for _ in range(count):
            if not self.cards:
                if self.refill_count < 2 and self.discard:
                    self.cards        = self.discard[:]
                    self.discard      = []
                    self.refill_count += 1
                    random.shuffle(self.cards)
                else:
                    break
            if self.cards:
                drawn.append(self.cards.pop())
        return drawn


# ==================== 玩家 ====================
class Player:
    def __init__(self, name):
        self.name  = name
        self.deck  = None       # 由外部赋值
        self.hand  = []
        self.slots = [None] * 5

        self.max_hp          = INITIAL_HP
        self.hp              = INITIAL_HP
        self.damage_bonus    = 0.0
        self.lifesteal       = 0.0
        self.damage_reduction = 0.0
        self.dodge_chance    = 0.0
        self.crit_rate       = 0.05
        self.crit_damage     = 0.5

    def draw_cards(self, count=DRAW_PER_TURN):
        max_hand = max(1, int(self.hp * 2))
        to_draw  = min(count, max_hand - len(self.hand))
        if to_draw > 0:
            self.hand.extend(self.deck.draw(to_draw))

    def place_card(self, card, slot):
        if 0 <= slot < 5 and card in self.hand and self.slots[slot] is None:
            self.hand.remove(card)
            self.slots[slot] = card
            return True
        return False

    def clear_slots(self):
        for c in self.slots:
            if c and not c.is_copy:
                self.deck.discard.append(c)
        self.slots = [None] * 5

    def is_dead(self):
        return self.hp <= 0.001


# ==================== 伤害结算上下文 ====================
class DamageContext:
    """封装单次伤害的完整结算流程（暴击/免伤/吸血/闪避）"""

    def __init__(self, attacker, defender, base_damage, atk_card=None):
        self.attacker     = attacker
        self.defender     = defender
        self.base_damage  = base_damage

        self.final_damage  = base_damage
        self.actual_damage = 0
        self.is_crit       = False
        self.is_dodge      = False
        self.vampire_amount = 0

        # 基础属性 + 牌自带加成
        card_crit_rate   = atk_card.crit_rate_bonus   if atk_card else 0.0
        card_crit_damage = atk_card.crit_damage_bonus if atk_card else 0.0

        # 使用属性工具类进行边界检查
        attribute_utils = get_attribute_utils()

        # 计算并限制属性值
        self.crit_rate        = attribute_utils.clamp_attribute("crit_rate", attacker.crit_rate + card_crit_rate)
        self.crit_damage      = attribute_utils.clamp_attribute("crit_damage", attacker.crit_damage + card_crit_damage)
        self.damage_bonus     = attribute_utils.clamp_attribute("damage_bonus", attacker.damage_bonus)
        self.damage_reduction = attribute_utils.clamp_attribute("damage_reduction", defender.damage_reduction)
        self.lifesteal        = attribute_utils.clamp_attribute("lifesteal", attacker.lifesteal)
        self.dodge_chance     = attribute_utils.clamp_attribute("dodge_chance", defender.dodge_chance)

    def calculate(self):
        import random
        if random.random() < self.dodge_chance:
            self.is_dodge      = True
            self.final_damage  = 0
            self.actual_damage = 0
            return self

        self.final_damage = self.base_damage * (1 + self.damage_bonus)

        if random.random() < self.crit_rate:
            self.is_crit       = True
            self.final_damage *= (1 + self.crit_damage)

        self.actual_damage = round(
            max(self.final_damage * (1 - self.damage_reduction), 0.001), 3
        )

        if self.lifesteal > 0 and self.actual_damage > 0:
            self.vampire_amount = round(self.actual_damage * self.lifesteal, 3)

        self.final_damage = round(self.final_damage, 3)
        return self

    def apply(self):
        if not self.is_dodge:
            self.defender.hp = round(max(self.defender.hp - self.actual_damage, 0.0), 3)
        if self.vampire_amount > 0:
            self.attacker.hp = round(
                min(self.attacker.hp + self.vampire_amount, self.attacker.max_hp), 3
            )
        return self


# ==================== 位置结算逻辑 ====================
class PositionBattleLogic:
    """
    双向同位置结算。
    resolve_battle 返回 steps 列表，每个 step 是一个 dict：
      {
        "pos": int,               # 位置索引 0-4
        "logs": [str, ...],       # 本步骤的文字日志
        "actions": [callable, ...]# 需要执行的伤害/吸血操作（无参 lambda）
      }
    调用方可逐步 apply 每个 step，实现动画。
    """

    @staticmethod
    def _make_hit_action(attacker, defender, multiplier, atk_card=None):
        """
        返回 (logs, action_fn)。
        atk_card 若为肘牌，则叠加其暴击加成。
        """
        ctx = DamageContext(attacker, defender, BASE_ATTACK * multiplier, atk_card)
        ctx.calculate()
        logs = []
        if ctx.is_dodge:
            logs.append(f"  结果：{defender.name}闪避了攻击！")
        else:
            if ctx.is_crit:
                logs.append(f"  💥 暴击！额外{ctx.crit_damage*100:.0f}%伤害")
            logs.append(f"  结果：{attacker.name}造成 {ctx.final_damage:.3f} 点伤害（免伤后{ctx.actual_damage:.3f}）")
            if ctx.vampire_amount > 0:
                logs.append(f"  🩸 吸血 {ctx.vampire_amount:.3f} 点")
        return logs, ctx.apply

    @staticmethod
    def resolve_battle(player, ai, player_slots, ai_slots):
        """
        返回 steps 列表，每个 step：
          {"pos": int, "logs": [str], "actions": [callable]}
        调用方按顺序执行 step["actions"] 后再处理下一步。
        """
        steps = []

        for pos in range(5):
            logs    = [f"--- 位置{pos+1}结算 ---"]
            actions = []

            p_card = player_slots[pos]
            a_card = ai_slots[pos]

            # ---- 偷牌 ----
            if p_card and p_card.card_type == "steal" and a_card:
                logs.append(f"  偷牌：玩家偷走电脑的 {a_card.name}{a_card.number}")
                _a = a_card
                def _steal_by_player(_a=_a, pos=pos):
                    player.hand.append(_a.make_copy())   # 玩家得到复制牌
                    ai.deck.discard.append(_a)            # 原牌进弃牌堆
                    ai.slots[pos] = None                  # 清除真实槽位
                actions.append(_steal_by_player)
                ai_slots[pos] = None
                a_card = None
            elif a_card and a_card.card_type == "steal" and p_card:
                logs.append(f"  偷牌：电脑偷走玩家的 {p_card.name}{p_card.number}")
                _p = p_card
                def _steal_by_ai(_p=_p, pos=pos):
                    ai.hand.append(_p.make_copy())        # 电脑得到复制牌
                    player.deck.discard.append(_p)        # 原牌进弃牌堆
                    player.slots[pos] = None              # 清除真实槽位
                actions.append(_steal_by_ai)
                player_slots[pos] = None
                p_card = None
            else:
                logs.append(f"  偷牌：无偷牌")

            p_card = player_slots[pos]
            a_card = ai_slots[pos]

            p_is_fist = p_card and p_card.card_type in ("fist", "elbow")
            a_is_fist = a_card and a_card.card_type in ("fist", "elbow")
            p_is_def  = p_card and p_card.card_type == "defend"
            a_is_def  = a_card and a_card.card_type == "defend"

            if not p_is_fist and not a_is_fist:
                logs.append(f"  攻击：无攻击")
                steps.append({"pos": pos, "logs": logs, "actions": actions})
                continue

            # 拳/肘 vs 拳/肘
            if p_is_fist and a_is_fist:
                if p_card.number == a_card.number:
                    logs.append(f"  攻击：玩家{p_card.name}{p_card.number} = 电脑{a_card.name}{a_card.number}（平局，各1.0倍）")
                    h1_logs, h1_fn = PositionBattleLogic._make_hit_action(player, ai, 1.0, p_card)
                    h2_logs, h2_fn = PositionBattleLogic._make_hit_action(ai, player, 1.0, a_card)
                    logs += h1_logs + h2_logs
                    actions += [h1_fn, h2_fn]
                elif p_card.number > a_card.number:
                    logs.append(f"  攻击：玩家{p_card.name}{p_card.number} > 电脑{a_card.name}{a_card.number}（玩家先手1.5倍）")
                    h1_logs, h1_fn = PositionBattleLogic._make_hit_action(player, ai, 1.5, p_card)
                    logs += h1_logs
                    actions.append(h1_fn)
                    def _p_counterattack(step={"pos": pos, "logs": logs, "actions": actions}, _ac=a_card):
                        if not ai.is_dead():
                            c_logs, c_fn = PositionBattleLogic._make_hit_action(ai, player, 1.0, _ac)
                            step["logs"].append(f"  攻击：电脑反击（1.0倍）")
                            step["logs"] += c_logs
                            c_fn()
                    actions.append(_p_counterattack)
                else:
                    logs.append(f"  攻击：电脑{a_card.name}{a_card.number} > 玩家{p_card.name}{p_card.number}（电脑先手1.5倍）")
                    h1_logs, h1_fn = PositionBattleLogic._make_hit_action(ai, player, 1.5, a_card)
                    logs += h1_logs
                    actions.append(h1_fn)
                    def _a_counterattack(step={"pos": pos, "logs": logs, "actions": actions}, _pc=p_card):
                        if not player.is_dead():
                            c_logs, c_fn = PositionBattleLogic._make_hit_action(player, ai, 1.0, _pc)
                            step["logs"].append(f"  攻击：玩家反击（1.0倍）")
                            step["logs"] += c_logs
                            c_fn()
                    actions.append(_a_counterattack)
                steps.append({"pos": pos, "logs": logs, "actions": actions})
                continue

            # 拳/肘 vs 防
            if p_is_fist and a_is_def:
                if p_card.number > a_card.number:
                    logs.append(f"  攻击：玩家{p_card.name}{p_card.number} 破电脑防{a_card.number}（0.2倍）")
                    h_logs, h_fn = PositionBattleLogic._make_hit_action(player, ai, 0.2, p_card)
                    logs += h_logs
                    actions.append(h_fn)
                else:
                    logs.append(f"  攻击：玩家{p_card.name}{p_card.number} 被电脑防{a_card.number}抵消")
                steps.append({"pos": pos, "logs": logs, "actions": actions})
                continue

            if a_is_fist and p_is_def:
                if a_card.number > p_card.number:
                    logs.append(f"  攻击：电脑{a_card.name}{a_card.number} 破玩家防{p_card.number}（0.2倍）")
                    h_logs, h_fn = PositionBattleLogic._make_hit_action(ai, player, 0.2, a_card)
                    logs += h_logs
                    actions.append(h_fn)
                else:
                    logs.append(f"  攻击：电脑{a_card.name}{a_card.number} 被玩家防{p_card.number}抵消")
                steps.append({"pos": pos, "logs": logs, "actions": actions})
                continue

            # 拳/肘 vs 空位
            if p_is_fist and not a_card:
                logs.append(f"  攻击：玩家{p_card.name}{p_card.number} 攻击空位（1.0倍）")
                h_logs, h_fn = PositionBattleLogic._make_hit_action(player, ai, 1.0, p_card)
                logs += h_logs
                actions.append(h_fn)

            if a_is_fist and not p_card:
                logs.append(f"  攻击：电脑{a_card.name}{a_card.number} 攻击空位（1.0倍）")
                h_logs, h_fn = PositionBattleLogic._make_hit_action(ai, player, 1.0, a_card)
                logs += h_logs
                actions.append(h_fn)

            steps.append({"pos": pos, "logs": logs, "actions": actions})

        return steps
