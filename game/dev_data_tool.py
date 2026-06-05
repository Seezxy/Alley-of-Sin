"""
测试人员存档调试工具
用法:
  python dev_data_tool.py view              # 查看当前存档
  python dev_data_tool.py set-currency <金额>  # 设置货币
  python dev_data_tool.py add-item <物品ID>    # 添加物品
  python dev_data_tool.py unlock-all         # 解锁全部物品
  python dev_data_tool.py reset             # 重置存档
  python dev_data_tool.py export <文件>      # 导出明文JSON
  python dev_data_tool.py import <文件>      # 导入明文JSON

需要 data/.dev_mode 文件存在或 GAME_DEV_MODE=1 环境变量
"""
import os
import sys
import json
import uuid
from datetime import datetime

# 切换到项目根目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from game.save_crypto import encrypt_data, decrypt_data

DATA_FILE = "data/users.dat"
ITEMS_FILE = "data/items.json"


def check_dev_mode():
    if not (os.path.exists("data/.dev_mode") or os.environ.get("GAME_DEV_MODE") == "1"):
        print("错误: 需要开启开发者模式")
        print("请创建 data/.dev_mode 文件或设置环境变量 GAME_DEV_MODE=1")
        sys.exit(1)


def load_data():
    if not os.path.exists(DATA_FILE):
        print("存档文件不存在，将创建空存档")
        return {"users": {}, "current_user": None}
    with open(DATA_FILE, "rb") as f:
        return decrypt_data(f.read())


def save_data(data):
    encrypted = encrypt_data(data)
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)
    print("已保存。")


def load_items():
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_view():
    data = load_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_set_currency(amount):
    data = load_data()
    user = _get_current_user(data)
    old = user.get("currency", 0)
    user["currency"] = int(amount)
    save_data(data)
    print(f"货币: {old} -> {amount}")


def cmd_add_item(item_id):
    data = load_data()
    items_db = load_items()
    if item_id not in items_db["items"]:
        print(f"错误: 物品 '{item_id}' 不存在")
        sys.exit(1)
    user = _get_current_user(data)
    inventory = user.setdefault("inventory", {"capacity": 5000, "items": []})
    instance_id = str(uuid.uuid4())
    inventory["items"].append({
        "instance_id": instance_id,
        "item_id": item_id,
        "equipped": False,
        "created_at": datetime.now().isoformat()
    })
    save_data(data)
    item_name = items_db["items"][item_id]["name"]
    print(f"已添加: {item_name} ({item_id})")


def cmd_unlock_all():
    data = load_data()
    items_db = load_items()
    user = _get_current_user(data)
    inventory = user.setdefault("inventory", {"capacity": 5000, "items": []})
    existing_ids = {item["item_id"] for item in inventory["items"]}
    added = 0
    for item_id in items_db["items"]:
        if item_id not in existing_ids:
            inventory["items"].append({
                "instance_id": str(uuid.uuid4()),
                "item_id": item_id,
                "equipped": False,
                "created_at": datetime.now().isoformat()
            })
            added += 1
    save_data(data)
    print(f"已解锁 {added} 件新物品（总计 {len(inventory['items'])} 件）")


def cmd_reset():
    confirm = input("确定要重置所有存档数据吗? [y/N]: ")
    if confirm.lower() == "y":
        data = {"users": {}, "current_user": None}
        save_data(data)
        print("存档已重置。")


def cmd_export(filepath):
    data = load_data()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已导出到: {filepath}")


def cmd_import(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    save_data(data)
    print(f"已从 {filepath} 导入。")


def _get_current_user(data):
    name = data.get("current_user")
    if not name:
        print("错误: 没有当前登录用户，请先启动游戏并创建一个用户。")
        sys.exit(1)
    if name not in data["users"]:
        print(f"错误: 用户 '{name}' 不存在")
        sys.exit(1)
    return data["users"][name]


def print_usage():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    check_dev_mode()
    cmd = sys.argv[1]

    if cmd == "view":
        cmd_view()
    elif cmd == "set-currency":
        if len(sys.argv) < 3:
            print("用法: python dev_data_tool.py set-currency <金额>")
            sys.exit(1)
        cmd_set_currency(sys.argv[2])
    elif cmd == "add-item":
        if len(sys.argv) < 3:
            print("用法: python dev_data_tool.py add-item <物品ID>")
            sys.exit(1)
        cmd_add_item(sys.argv[2])
    elif cmd == "unlock-all":
        cmd_unlock_all()
    elif cmd == "reset":
        cmd_reset()
    elif cmd == "export":
        if len(sys.argv) < 3:
            print("用法: python dev_data_tool.py export <文件路径>")
            sys.exit(1)
        cmd_export(sys.argv[2])
    elif cmd == "import":
        if len(sys.argv) < 3:
            print("用法: python dev_data_tool.py import <文件路径>")
            sys.exit(1)
        cmd_import(sys.argv[2])
    else:
        print(f"未知命令: {cmd}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
