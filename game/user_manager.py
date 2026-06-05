"""
用户数据管理模块
负责用户数据的加载、保存、验证和管理
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any, List

from game.save_crypto import encrypt_data, decrypt_data, migrate_plaintext_to_encrypted
from cryptography.fernet import InvalidToken
from game.resource_utils import get_user_data_path


def _migrate_existing_encrypted(old_path: str, new_path: str):
    """将旧位置的加密文件迁移到新位置"""
    import shutil
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.copy2(old_path, new_path)
    os.remove(old_path)
    print(f"已迁移加密存档: {old_path} -> {new_path}")


class UserManager:
    """用户数据管理器"""

    def __init__(self, data_file: str = None):
        """
        初始化用户管理器

        Args:
            data_file: 用户数据文件路径，如果为None则自动选择
        """
        if data_file is None:
            # 使用用户AppData固定目录，程序移动后存档不丢失
            self.data_file = get_user_data_path("users.dat")
        else:
            self.data_file = data_file

        self.users: Dict[str, Dict] = {}
        self.current_user: Optional[str] = None
        self.load_data()

    def load_data(self) -> None:
        """加载用户数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    encrypted = f.read()
                data = decrypt_data(encrypted)
                self.users = data.get("users", {})
                self.current_user = data.get("current_user")
            else:
                # 尝试迁移旧文件（按优先级：项目目录旧加密 → 项目目录旧明文 → AppData旧明文）
                old_enc = "data/users.dat"
                old_json = "data/users.json"
                if os.path.exists(old_enc):
                    _migrate_existing_encrypted(old_enc, self.data_file)
                    self.load_data()
                    return
                if os.path.exists(old_json):
                    if migrate_plaintext_to_encrypted(old_json, self.data_file):
                        self.load_data()
                        return
                self.users = {}
                self.current_user = None
                self.save_data()
        except (InvalidToken, json.JSONDecodeError, IOError) as e:
            print(f"加载用户数据失败: {e}")
            self.users = {}
            self.current_user = None

    def save_data(self) -> bool:
        """保存用户数据"""
        try:
            data = {
                "users": self.users,
                "current_user": self.current_user
            }

            encrypted = encrypt_data(data)
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            with open(self.data_file, 'wb') as f:
                f.write(encrypted)
            return True
        except IOError as e:
            print(f"保存用户数据失败: {e}")
            return False

    def validate_nickname(self, nickname: str) -> tuple[bool, str]:
        """
        验证昵称

        Args:
            nickname: 用户昵称

        Returns:
            (是否有效, 错误消息)
        """
        # 检查长度
        if len(nickname) < 1:
            return False, "昵称不能为空"
        if len(nickname) > 50:
            return False, "昵称不能超过50个字符"

        # 检查是否已存在
        if nickname in self.users:
            return False, "该昵称已存在"

        return True, ""

    def user_exists(self, nickname: str) -> bool:
        """检查用户是否存在"""
        return nickname in self.users

    def create_user(self, nickname: str) -> bool:
        """
        创建新用户

        Args:
            nickname: 用户昵称

        Returns:
            是否创建成功
        """
        # 验证昵称
        is_valid, error_msg = self.validate_nickname(nickname)
        if not is_valid:
            print(f"创建用户失败: {error_msg}")
            return False

        # 创建用户数据
        now = datetime.now().isoformat()
        self.users[nickname] = {
            "id": nickname,
            "created_at": now,
            "last_login": now,
            "game_stats": {
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "highest_stage": 0
            },
            "preferences": {
                "last_character": "loulo",
                "last_difficulty": 1
            },
            # 背包系统字段
            "inventory": {
                "capacity": 5000,
                "items": []
            },
            "equipment": {
                "weapon": None,
                "armor": None,
                "accessory": None
            },
            # 货币系统字段
            "currency": 0  # 初始货币为0
        }

        # 设置为当前用户
        self.current_user = nickname

        # 保存数据
        return self.save_data()

    def login_user(self, nickname: str) -> bool:
        """
        登录用户

        Args:
            nickname: 用户昵称

        Returns:
            是否登录成功
        """
        if nickname not in self.users:
            return False

        # 更新最后登录时间
        self.users[nickname]["last_login"] = datetime.now().isoformat()
        self.current_user = nickname

        # 保存数据
        return self.save_data()

    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户数据"""
        if self.current_user and self.current_user in self.users:
            return self.users[self.current_user]
        return None

    def get_current_nickname(self) -> Optional[str]:
        """获取当前用户昵称"""
        return self.current_user

    def update_user_stats(self, game_result: Dict[str, Any]) -> bool:
        """
        更新用户游戏统计数据

        Args:
            game_result: 游戏结果数据

        Returns:
            是否更新成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        user = self.users[self.current_user]
        stats = user["game_stats"]

        # 更新统计数据
        stats["total_games"] = stats.get("total_games", 0) + 1

        if game_result.get("won"):
            stats["wins"] = stats.get("wins", 0) + 1
        else:
            stats["losses"] = stats.get("losses", 0) + 1

        # 更新最高阶段
        stage_reached = game_result.get("stage_reached", 0)
        if stage_reached > stats.get("highest_stage", 0):
            stats["highest_stage"] = stage_reached

        return self.save_data()

    def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        更新用户偏好设置

        Args:
            preferences: 偏好设置

        Returns:
            是否更新成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        user = self.users[self.current_user]
        user_prefs = user["preferences"]

        # 更新偏好设置
        for key, value in preferences.items():
            user_prefs[key] = value

        return self.save_data()

    def get_all_users(self) -> Dict[str, Dict]:
        """获取所有用户数据"""
        return self.users.copy()

    def switch_user(self, nickname: str) -> bool:
        """
        切换用户

        Args:
            nickname: 要切换到的用户昵称

        Returns:
            是否切换成功
        """
        if nickname not in self.users:
            return False

        self.current_user = nickname
        return self.save_data()

    # ==================== 背包系统方法 ====================

    def get_inventory(self) -> Dict[str, Any]:
        """获取当前用户的背包数据"""
        if not self.current_user or self.current_user not in self.users:
            return {"capacity": 5000, "items": []}

        user = self.users[self.current_user]
        inventory = user.get("inventory", {"capacity": 5000, "items": []})

        # 确保容量至少为5000
        if inventory.get("capacity", 0) < 5000:
            inventory["capacity"] = 5000

        return inventory

    def get_equipment(self) -> Dict[str, Optional[str]]:
        """获取当前用户的装备数据"""
        if not self.current_user or self.current_user not in self.users:
            return {"weapon": None, "armor": None, "accessory": None}

        user = self.users[self.current_user]
        return user.get("equipment", {"weapon": None, "armor": None, "accessory": None})

    def add_item_to_inventory(self, item_instance: Dict[str, Any], save: bool = True) -> bool:
        """
        添加物品到背包

        Args:
            item_instance: 物品实例数据
            save: 是否立即保存到磁盘

        Returns:
            是否添加成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        user = self.users[self.current_user]
        inventory = user.get("inventory", {"capacity": 5000, "items": []})

        # 确保容量至少为5000
        if inventory.get("capacity", 0) < 5000:
            inventory["capacity"] = 5000

        # 检查背包容量
        if len(inventory.get("items", [])) >= inventory.get("capacity", 5000):
            return False

        # 添加物品
        inventory.setdefault("items", []).append(item_instance)
        return self.save_data() if save else True

    def remove_item_from_inventory(self, instance_id: str, save: bool = True) -> bool:
        """
        从背包移除物品

        Args:
            instance_id: 物品实例ID
            save: 是否立即保存到磁盘

        Returns:
            是否移除成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        user = self.users[self.current_user]
        inventory = user.get("inventory", {"capacity": 20, "items": []})

        # 查找并移除物品
        items = inventory.get("items", [])
        for i, item in enumerate(items):
            if item.get("instance_id") == instance_id:
                items.pop(i)
                return self.save_data() if save else True

        return False

    def equip_item(self, instance_id: str, slot: str) -> bool:
        """
        装备物品

        Args:
            instance_id: 物品实例ID
            slot: 装备槽位（weapon/armor/accessory）

        Returns:
            是否装备成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        if slot not in ["weapon", "armor", "accessory"]:
            return False

        user = self.users[self.current_user]
        inventory = user.get("inventory", {"capacity": 20, "items": []})
        equipment = user.get("equipment", {"weapon": None, "armor": None, "accessory": None})

        # 查找物品
        target_item = None
        item_index = -1
        items = inventory.get("items", [])

        for i, item in enumerate(items):
            if item.get("instance_id") == instance_id:
                target_item = item
                item_index = i
                break

        if not target_item:
            return False

        # 检查当前槽位是否有装备，有则先卸下
        current_equipped = equipment.get(slot)
        if current_equipped:
            # 找到当前装备的物品并标记为未装备
            for item in items:
                if item.get("instance_id") == current_equipped:
                    item["equipped"] = False
                    break

        # 装备新物品
        target_item["equipped"] = True
        equipment[slot] = instance_id

        return self.save_data()

    def unequip_item(self, slot: str) -> bool:
        """
        卸下装备

        Args:
            slot: 装备槽位（weapon/armor/accessory）

        Returns:
            是否卸下成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        if slot not in ["weapon", "armor", "accessory"]:
            return False

        user = self.users[self.current_user]
        equipment = user.get("equipment", {"weapon": None, "armor": None, "accessory": None})
        inventory = user.get("inventory", {"capacity": 20, "items": []})

        instance_id = equipment.get(slot)
        if not instance_id:
            return False

        # 找到物品并标记为未装备
        items = inventory.get("items", [])
        for item in items:
            if item.get("instance_id") == instance_id:
                item["equipped"] = False
                break

        # 清空装备槽位
        equipment[slot] = None

        return self.save_data()

    def get_equipped_items(self) -> Dict[str, Optional[Dict]]:
        """
        获取当前装备的物品详情

        Returns:
            装备槽位到物品详情的映射
        """
        if not self.current_user or self.current_user not in self.users:
            return {"weapon": None, "armor": None, "accessory": None}

        user = self.users[self.current_user]
        equipment = user.get("equipment", {"weapon": None, "armor": None, "accessory": None})
        inventory = user.get("inventory", {"capacity": 20, "items": []})

        result = {"weapon": None, "armor": None, "accessory": None}

        for slot, instance_id in equipment.items():
            if instance_id:
                # 在背包中查找物品
                for item in inventory.get("items", []):
                    if item.get("instance_id") == instance_id:
                        result[slot] = item
                        break

        return result

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """获取背包中的所有物品"""
        if not self.current_user or self.current_user not in self.users:
            return []

        user = self.users[self.current_user]
        inventory = user.get("inventory", {"capacity": 20, "items": []})
        return inventory.get("items", []).copy()

    # ==================== 货币系统方法 ====================

    def get_currency(self) -> int:
        """获取当前用户的货币数量"""
        if not self.current_user or self.current_user not in self.users:
            return 0

        user = self.users[self.current_user]
        return user.get("currency", 0)

    def add_currency(self, amount: int, save: bool = True) -> bool:
        """
        为当前用户添加货币

        Args:
            amount: 要添加的货币数量
            save: 是否立即保存到磁盘

        Returns:
            是否添加成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        if amount <= 0:
            return False

        user = self.users[self.current_user]
        current_currency = user.get("currency", 0)
        user["currency"] = current_currency + amount

        return self.save_data() if save else True

    def set_currency(self, amount: int, save: bool = True) -> bool:
        """
        直接设置当前用户的货币数量

        Args:
            amount: 要设置的货币数量
            save: 是否立即保存到磁盘

        Returns:
            是否设置成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        if amount < 0:
            amount = 0

        user = self.users[self.current_user]
        user["currency"] = amount

        return self.save_data() if save else True

    def deduct_currency(self, amount: int, save: bool = True) -> bool:
        """
        从当前用户扣除货币

        Args:
            amount: 要扣除的货币数量
            save: 是否立即保存到磁盘

        Returns:
            是否扣除成功
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        if amount <= 0:
            return False

        user = self.users[self.current_user]
        current_currency = user.get("currency", 0)

        if current_currency < amount:
            return False  # 货币不足

        user["currency"] = current_currency - amount
        return self.save_data() if save else True

    def has_enough_currency(self, amount: int) -> bool:
        """
        检查当前用户是否有足够的货币

        Args:
            amount: 需要的货币数量

        Returns:
            是否有足够的货币
        """
        if not self.current_user or self.current_user not in self.users:
            return False

        user = self.users[self.current_user]
        current_currency = user.get("currency", 0)
        return current_currency >= amount

    def format_currency(self, amount: int = None) -> str:
        """
        格式化货币显示

        Args:
            amount: 货币数量，如果为None则使用当前用户的货币数量

        Returns:
            格式化后的货币字符串
        """
        from game.constants import CURRENCY_SYMBOL, CURRENCY_FORMAT

        if amount is None:
            amount = self.get_currency()

        return CURRENCY_FORMAT.format(symbol=CURRENCY_SYMBOL, amount=amount)


# 单例实例
_user_manager_instance = None

def get_user_manager() -> UserManager:
    """获取用户管理器单例实例"""
    global _user_manager_instance
    if _user_manager_instance is None:
        _user_manager_instance = UserManager()
    return _user_manager_instance