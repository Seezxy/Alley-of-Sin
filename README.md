# 罪恶巷口 (Sin Alley) 🥊

街头格斗锦标赛卡牌游戏。从 64 强一路打到冠军。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行游戏
python main.py
# 或者
python -m game
```

## 玩法简介

1. 选择模式 → 选择角色 → 进入锦标赛
2. 每回合把手牌拖到 1~5 个位置，点「确认出牌」
3. 点「开始结算」，双方按位置逐一对比
4. 血量归零者失败，胜利后选择一项属性强化

## 卡牌类型

| 牌 | 作用 |
|----|------|
| 🟥 拳 | 攻击，数字越大越强 |
| 🟦 防 | 防御，数字越大越难破 |
| 🟪 偷 | 复制对位的牌到手牌 |

## 项目结构

```
sin-alley/
├── main.py              # 入口
├── game/                # 游戏主包
│   ├── app.py           # Game 主控类
│   ├── constants.py     # 常量配置
│   ├── models.py        # 数据模型
│   ├── card_battle.py   # 卡牌对战核心
│   ├── tournament.py    # 锦标赛模式
│   ├── endless_mode.py  # 无尽模式
│   ├── gacha_*.py       # 抽卡系统
│   ├── smelting_*.py    # 熔炼系统
│   ├── inventory*.py    # 背包系统
│   ├── item_*.py        # 物品管理
│   ├── catalogue_*.py   # 图鉴系统
│   ├── user_manager.py  # 用户/存档管理
│   ├── save_crypto.py   # 存档加密
│   └── ...
├── data/                # 游戏数据
├── images/              # 游戏图片资源
├── prompts/             # AI 生图提示词
├── scripts/             # 启动/打包脚本
└── docs/                # 文档
```

## 依赖

- Python 3.7+
- Pillow (图片处理)
- cryptography (存档加密)
- pypinyin (中文拼音排序, 可选)

## 开发者模式

在 `data/` 目录下创建 `.dev_mode` 文件，或设置环境变量 `GAME_DEV_MODE=1` 启用开发者面板。

## 打包

```bash
# 使用打包脚本
scripts/pack.bat

# 或手动
pip install pyinstaller
python -m PyInstaller --clean --noconsole --onefile \
  --name 罪恶巷口 \
  --add-data "images;images" \
  --add-data "data;data" \
  --hidden-import game \
  main.py
```

## 许可

MIT License - 详见 [LICENSE](LICENSE)
