# 罪恶巷口 (Alley of Sin) 🥊

> 一款基于 Python tkinter 的街头格斗锦标赛卡牌游戏。从 64 强一路打到冠军。

![Python](https://img.shields.io/badge/Python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 快速开始

```bash
pip install -r requirements.txt
python main.py
# 或 python -m game
```

## 玩法简介

1. 选择模式 → 选择角色 → 进入锦标赛
2. 每回合把手牌拖到 1~5 个位置，点「确认出牌」
3. 点「开始结算」，双方按位置逐一对比
4. 血量归零者失败，胜利后选择一项属性强化

## 卡牌系统

| 牌 | 效果 | 机制 |
|----|------|------|
| 🟥 **拳** | 攻击牌 | 数字越大伤害越高，拳拳对决触发先手/反击机制 |
| 🟦 **防** | 防御牌 | 拳 ≤ 防时攻击被完全抵消，拳 > 防时仅造成 20% 伤害 |
| 🟪 **偷** | 复制牌 | 复制对方同位置卡牌加入手牌，原牌进入弃牌堆 |

### 结算规则

- **拳 vs 拳**：数值大者以 1.5× 先手出击，对方未倒下则 1.0× 反击；平局双方同时 1.0×
- **拳 vs 防**：破防仅造成 0.2× 伤害，未破防则完全抵消
- **拳 vs 空位**：直接 1.0× 伤害
- **偷牌**：获得对位牌复制，本位置不攻击

### 角色属性

| 属性 | 效果 |
|------|------|
| 伤害加成 | 出牌伤害倍率提升 |
| 暴击率 / 暴击伤害 | 概率触发额外伤害 |
| 免伤 | 承受伤害 × (1 − 免伤) |
| 吸血 | 造成伤害的比例回复生命 |
| 闪避 | 概率完全免疫一次攻击 |

## 技术架构

```
Alley of Sin/
├── main.py              # 程序入口，窗口初始化
├── game/                # 游戏主包（27 个模块）
│   ├── app.py           # 主控类，界面路由与生命周期管理
│   ├── card_battle.py   # 卡牌对战核心引擎（≈1500 行）
│   ├── tournament.py    # 锦标赛流程控制（64→32→…→冠军）
│   ├── endless_mode.py  # 无尽模式，难度递增
│   ├── models.py        # 数据模型（玩家、对手、AI）
│   ├── constants.py     # 全局常量与配置
│   ├── gacha_*.py       # 抽卡系统（概率池 + UI）
│   ├── smelting_*.py    # 熔炼系统（装备合成）
│   ├── inventory*.py    # 背包系统（拖拽 + 排序）
│   ├── catalogue_*.py   # 图鉴系统
│   ├── user_manager.py  # 用户/存档管理（多账号）
│   ├── save_crypto.py   # 存档加密（AES-GCM + HMAC）
│   └── resource_utils.py # 资源路径解析（兼容 PyInstaller 打包）
├── data/                # 游戏静态数据（JSON）
└── images/              # 游戏图片资源
```

### 技术要点

- **纯 Python + tkinter**：无游戏引擎依赖，原生 GUI 实现完整的回合制卡牌对战
- **存档加密**：基于 `cryptography` 库的 Fernet 方案（AES-128-GCM + HMAC），保障玩家数据安全
- **延迟导入 + 懒加载**：各界面按需实例化，减少启动时间和内存占用
- **自定义事件路由**：`show_frame` 实现界面栈管理，支持前后切换
- **资源路径抽象**：`get_resource_path` 统一处理开发环境与 PyInstaller 打包后的路径差异
- **可配置抽卡池**：概率、卡池、保底机制均通过 JSON 配置，无需改代码
- **开发者面板**：内置调试工具，支持属性编辑、资源热加载等

## 依赖

| 库 | 用途 |
|----|------|
| Pillow | 图片加载与处理 |
| cryptography | 存档加密（Fernet） |
| pypinyin | 中文拼音排序（可选） |

## 打包

```bash
pip install pyinstaller
python -m PyInstaller --clean --noconsole --onefile \
  --name 罪恶巷口 \
  --add-data "images;images" \
  --add-data "data;data" \
  --hidden-import game \
  main.py
```

## License

MIT License — 详见 [LICENSE](LICENSE)
