"""
游戏常量定义
"""

# 界面常量
WINDOW_TITLE = "罪恶巷口"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 720  # 增加20%

# 阶段定义
STAGES = [
    "64强",
    "32强",
    "16强",
    "8强",
    "4强",
    "半决赛",
    "决赛",
    "冠军"
]

# 各阶段 AI 属性由 tournament.py 动态随机生成，无需静态配置



# 默认牌库配置（各角色可覆盖）
DEFAULT_DECK = {
    "fist": 30,   # 拳牌数量
    "defend": 20, # 防牌数量
    "steal": 10,  # 偷牌数量
}

# 角色信息
CHARACTERS = {
    "loulo": {
        "name": "喽啰",
        "desc": "罪恶巷口的小混混，属性均衡\n适合新手入门的均衡角色\n基础属性无特殊加成",
        "max_hp": 10,
        "damage_bonus": 0.0,
        "lifesteal": 0.0,
        "damage_reduction": 0.0,
        "dodge_chance": 0.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "deck": DEFAULT_DECK,  # 使用默认牌库
    },
    "taiquan": {
        "name": "泰拳手",
        "desc": "牌库含10张肘牌（序号2-20偶数）\n肘牌：暴击率+50%，暴击额外伤害+100%\n破防能力强，暴击伤害爆发高",
        "max_hp": 10,
        "damage_bonus": 0.0,
        "lifesteal": 0.0,
        "damage_reduction": 0.0,
        "dodge_chance": 0.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "deck": {"fist": 20, "elbow": 10, "defend": 20, "steal": 10},
    },
    "dashou": {
        "name": "打手",
        "desc": "街头混混，伤害加成5%，免伤5%\n攻防均衡的街头战士\n兼顾输出与生存能力",
        "max_hp": 10,
        "damage_bonus": 0.05,
        "lifesteal": 0.0,
        "damage_reduction": 0.05,
        "dodge_chance": 0.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "deck": DEFAULT_DECK,
    },
    "thief": {
        "name": "小偷",
        "desc": "牌库含20张偷牌（替换10张拳牌）\n偷牌战术专家，擅长夺取对手能力\n策略型角色，适合控制打法",
        "max_hp": 9,#角色较强，略微削弱血量
        "damage_bonus": 0.0,
        "lifesteal": 0.0,
        "damage_reduction": 0.0,
        "dodge_chance": 0.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "deck": {"fist": 20, "defend": 20, "steal": 20},
    },
    "programmer": {
        "name": "程序员",
        "desc": "测试专用角色\n伤害加成1000%，免伤95%\n用于测试赢了的结果",
        "max_hp": 10,
        "damage_bonus": 10.0,        # 1000%伤害加成
        "lifesteal": 0.0,
        "damage_reduction": 0.95,   # 95%免伤
        "dodge_chance": 0.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "deck": DEFAULT_DECK,       # 使用默认牌库
    },
    # "dage": {
    #     "name": "大哥",
    #     "desc": "巷口老大，血量高、伤害高",
    #     "max_hp": 15,
    #     "damage_bonus": 0.2,
    #     "lifesteal": 0.1,
    #     "damage_reduction": 0.1,
    #     "dodge_chance": 0.05,
    #     "crit_rate": 0.08,
    #     "crit_damage": 0.6,
    #     "deck": {"fist": 40, "defend": 10, "steal": 10},  # 偏攻击型牌库
    # }
}

# 登录相关常量
LOGIN_TITLE = "罪恶巷口 - 用户登录"
LOGIN_BUTTON_TEXT = "开始游戏"
USER_INFO_LABEL = "当前用户: "
NICKNAME_MIN_LENGTH = 1
NICKNAME_MAX_LENGTH = 50

# 颜色主题 - 暗黑街头风格
COLORS = {
    # 背景色系 - 层次化灰度
    "background": "#121212",        # 主背景 - 深灰黑
    "secondary_bg": "#1a1a1a",     # 次级背景 - 略亮
    "panel_bg": "#1e1e1e",         # 面板背景
    "card_bg": "#252525",          # 卡片背景
    "header_bg": "#2a2a2a",        # 标题区域背景

    # 交互元素
    "button": "#2d2d2d",           # 按钮背景 - 中灰
    "button_hover": "#333333",     # 按钮悬停
    "button_active": "#3a3a3a",    # 按钮激活
    "button_disabled": "#555555",  # 禁用按钮颜色

    # 文字
    "text": "#ffffff",             # 主要文字颜色
    "text_secondary": "#b0b0b0",   # 次级文字
    "text_muted": "#808080",       # 弱化文字

    # 语义色
    "success": "#4CAF50",          # 成功 - 绿色
    "success_light": "#81C784",    # 成功浅色
    "danger": "#F44336",           # 危险 - 红色
    "danger_light": "#E57373",     # 危险浅色
    "warning": "#FF9800",          # 警告 - 橙色
    "warning_light": "#FFB74D",    # 警告浅色
    "info": "#2196F3",             # 信息 - 蓝色
    "info_light": "#64B5F6",       # 信息浅色

    # 边框和分隔线
    "border": "#404040",           # 边框颜色
    "border_light": "#505050",     # 浅边框
    "divider": "#333333",          # 分隔线

    # 特殊用途
    "highlight": "#FFD700",        # 高亮色 - 金色
    "highlight_dark": "#B8860B",   # 深金色
    "dark_purple": "#4A235A",      # 暗紫色 - 用于边框

    # 登录界面
    "login_bg": "#1a1a1a",         # 登录界面背景
    "input_bg": "#252525",         # 输入框背景
    "input_border": "#404040",     # 输入框边框
    "user_info_bg": "#2a2a2a",     # 用户信息背景
}

# ==================== 背包系统常量 ====================

# 背包容量
INVENTORY_CAPACITY = 1000

# 物品稀有度颜色
RARITY_COLORS = {
    "common": "#808080",      # 灰色 - 普通
    "fine": "#FFFFFF",        # 白色 - 精品
    "uncommon": "#4CAF50",    # 绿色 - 优秀
    "rare": "#2196F3",        # 蓝色 - 罕见
    "epic": "#9C27B0",        # 紫色 - 史诗
    "legendary": "#FFD700",   # 金色 - 传说
    "mythical": "#FF0000",    # 红色 - 神话
}

# 物品类型
ITEM_TYPES = {
    "weapon": "武器",
    "armor": "护甲",
    "accessory": "饰品",
    "consumable": "消耗品",
    "material": "材料",
}

# 装备槽位
EQUIPMENT_SLOTS = {
    "weapon": "武器",
    "armor": "护甲",
    "accessory": "饰品",
}

# 背包界面常量
INVENTORY_WINDOW_TITLE = "背包"
INVENTORY_WINDOW_WIDTH = 800
INVENTORY_WINDOW_HEIGHT = 600

# 物品属性显示名称
ATTRIBUTE_DISPLAY_NAMES = {
    "max_hp": "最大生命值",
    "damage_bonus": "伤害加成",
    "lifesteal": "生命偷取",
    "damage_reduction": "伤害减免",
    "dodge_chance": "闪避几率",
    "crit_rate": "暴击率",
    "crit_damage": "暴击伤害",
    "defense": "防御力",
    "strength": "力量",
    "agility": "敏捷",
    "intelligence": "智力",
}

# ==================== 货币系统常量 ====================

# 货币名称
CURRENCY_NAME = "钞票"
CURRENCY_SYMBOL = "💵"

# 难度对应的货币奖励（已减半）
DIFFICULTY_REWARDS = {
    0: 30,   # 简单模式：30钞票
    1: 60,   # 标准模式：60钞票
    2: 120,  # 困难模式：120钞票
    3: 240,  # 地狱模式：240钞票
}

# 货币显示格式
CURRENCY_FORMAT = "{symbol} {amount}"

# ==================== 抽奖系统常量 ====================

# 抽奖价格
GACHA_PRICE = 60  # 一抽60钞票
GACHA_TEN_PRICE = 600  # 十连抽600钞票
GACHA_HUNDRED_PRICE = 6000  # 百连抽6000钞票

# 抽奖概率（百分比）
GACHA_PROBABILITIES = {
    "common": 60.0,     # 普通 60%
    "fine": 24.0,       # 精品 24%
    "uncommon": 11.0,   # 优秀 11%
    "rare": 3.0,        # 罕见 3%
    "epic": 1.5,        # 史诗 1.5%
    "legendary": 0.4,   # 传说 0.4%
    "mythical": 0.1     # 神话 0.1%
}

# 抽奖池类型
GACHA_POOLS = {
    "weapon": "武器池",
    "armor": "护甲池",
    "accessory": "饰品池",
    "all": "全部装备"
}

# 抽奖类型
GACHA_TYPES = {
    "single": "单抽",
    "ten": "十连抽",
    "max": "尽数抽"
}

# ==================== 无尽模式常量 ====================

# 无尽模式配置
ENDLESS_MODE_CONFIG = {
    "base_difficulty": 3,           # 固定为地狱难度
    "base_reward": 3,               # 第一场胜利奖金（基础奖金3）
    "reward_multiplier": 2,         # 奖金翻倍倍数
    "max_streak_display": 999,      # 最大连胜显示
    "ai_rewards_per_round": 3,      # 每轮AI获得强化数
    "max_damage_reduction": 0.99,   # 免伤上限（玩家和电脑）
}

# 无尽模式界面文本
ENDLESS_TEXTS = {
    "title": "无尽模式",
    "round_prefix": "第",
    "round_suffix": "场",
    "win_streak": "当前连胜",
    "current_reward": "本场奖金",
    "total_reward": "累计奖金",
    "start_battle": "⚔️ 开始战斗",
    "continue_battle": "⚔️ 继续战斗",
    "end_battle": "💰 结束战斗并结算",
    "settlement_title": "无尽模式结算",
    "settlement_streak": "连胜场次",
    "settlement_reward": "获得奖金",
    "early_exit": "主动结束",
}
