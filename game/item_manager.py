"""
物品管理器
负责加载和管理物品定义数据
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

# 尝试导入资源工具
try:
    from game.resource_utils import get_resource_path, load_json_resource
    USE_RESOURCE_UTILS = True
except ImportError:
    USE_RESOURCE_UTILS = False

# 导入属性工具类
from game.attribute_utils import get_attribute_utils


class ItemManager:
    """物品管理器"""

    def __init__(self, items_file: str = None):
        """
        初始化物品管理器

        Args:
            items_file: 物品定义文件路径，如果为None则自动选择
        """
        if items_file is None:
            if USE_RESOURCE_UTILS:
                # 使用资源工具获取资源路径
                self.items_file = get_resource_path("data/items.json")
            else:
                # 开发环境使用默认路径
                self.items_file = "data/items.json"
        else:
            self.items_file = items_file

        self.items: Dict[str, Dict] = {}
        self.item_types: Dict[str, Dict] = {}
        self.rarities: Dict[str, Dict] = {}
        self.equipment_slots: Dict[str, Dict] = {}
        self.load_items()

    def load_items(self) -> bool:
        """加载物品定义数据"""
        try:
            if USE_RESOURCE_UTILS:
                # 使用资源工具加载
                data = load_json_resource("data/items.json", {})
                self.items = data.get("items", {})
                self.item_types = data.get("item_types", {})
                self.rarities = data.get("rarities", {})
                self.equipment_slots = data.get("equipment_slots", {})
                return True
            else:
                # 原始加载方式
                if os.path.exists(self.items_file):
                    with open(self.items_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.items = data.get("items", {})
                        self.item_types = data.get("item_types", {})
                        self.rarities = data.get("rarities", {})
                        self.equipment_slots = data.get("equipment_slots", {})
                    return True
                else:
                    print(f"物品定义文件不存在: {self.items_file}")
                    return False
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载物品数据失败: {e}")
            return False

    def get_item(self, item_id: str) -> Optional[Dict]:
        """获取物品定义"""
        return self.items.get(item_id)

    def get_item_type(self, type_id: str) -> Optional[Dict]:
        """获取物品类型信息"""
        return self.item_types.get(type_id)

    def get_rarity(self, rarity_id: str) -> Optional[Dict]:
        """获取稀有度信息"""
        return self.rarities.get(rarity_id)

    def get_equipment_slot(self, slot_id: str) -> Optional[Dict]:
        """获取装备槽位信息"""
        return self.equipment_slots.get(slot_id)

    def create_item_instance(self, item_id: str, quantity: int = 1) -> Optional[Dict]:
        """
        创建物品实例

        Args:
            item_id: 物品ID
            quantity: 数量

        Returns:
            物品实例数据，或None如果物品不存在
        """
        item_def = self.get_item(item_id)
        if not item_def:
            return None

        # 创建物品实例
        instance = {
            "item_id": item_id,
            "instance_id": f"{item_id}_{uuid.uuid4().hex[:8]}",
            "quantity": min(quantity, item_def.get("max_stack", 1)),
            "acquired_at": datetime.now().isoformat(),
            "equipped": False
        }

        return instance

    def get_items_by_type(self, item_type: str) -> List[Dict]:
        """获取指定类型的物品"""
        return [item for item in self.items.values() if item.get("type") == item_type]

    def get_items_by_rarity(self, rarity: str) -> List[Dict]:
        """获取指定稀有度的物品"""
        return [item for item in self.items.values() if item.get("rarity") == rarity]

    def validate_item(self, item_id: str) -> tuple[bool, str]:
        """
        验证物品ID是否有效

        Args:
            item_id: 物品ID

        Returns:
            (是否有效, 错误消息)
        """
        if item_id not in self.items:
            return False, f"物品不存在: {item_id}"

        return True, ""

    def get_item_attributes(self, item_id: str) -> Dict[str, float]:
        """获取物品属性"""
        item = self.get_item(item_id)
        if not item:
            return {}

        return item.get("attributes", {}).copy()

    def can_equip_item(self, item_id: str, slot_id: str) -> tuple[bool, str]:
        """
        检查物品是否可以装备到指定槽位

        Args:
            item_id: 物品ID
            slot_id: 槽位ID

        Returns:
            (是否可以装备, 错误消息)
        """
        item = self.get_item(item_id)
        if not item:
            return False, f"物品不存在: {item_id}"

        item_type = item.get("type")
        if not item_type:
            return False, "物品没有类型定义"

        # 检查物品类型是否匹配槽位
        item_type_info = self.get_item_type(item_type)
        if not item_type_info:
            return False, f"物品类型无效: {item_type}"

        expected_slot = item_type_info.get("slot")
        if expected_slot != slot_id:
            return False, f"物品类型'{item_type}'不能装备到'{slot_id}'槽位"

        return True, ""

    def get_all_items(self) -> Dict[str, Dict]:
        """获取所有物品定义"""
        return self.items.copy()

    def get_item_display_name(self, item_id: str) -> str:
        """获取物品显示名称（包含稀有度颜色标记）"""
        item = self.get_item(item_id)
        if not item:
            return item_id

        rarity = self.get_rarity(item.get("rarity", "common"))
        if rarity:
            # 在实际UI中会使用颜色，这里只返回名称
            return item.get("name", item_id)

        return item.get("name", item_id)

    def get_item_description(self, item_id: str) -> str:
        """获取物品描述"""
        item = self.get_item(item_id)
        if not item:
            return ""

        description = item.get("description", "")
        attributes = item.get("attributes", {})

        # 添加属性描述
        if attributes:
            attr_descriptions = []
            attribute_utils = get_attribute_utils()

            for attr_name, attr_value in attributes.items():
                # 使用属性工具类格式化属性
                formatted_attr = attribute_utils.format_attribute_for_display(attr_name, attr_value)
                attr_descriptions.append(formatted_attr)

            if attr_descriptions:
                description += "\n\n" + "\n".join(attr_descriptions)

        return description


# 单例实例
_item_manager_instance = None

def get_item_manager() -> ItemManager:
    """获取物品管理器单例实例"""
    global _item_manager_instance
    if _item_manager_instance is None:
        _item_manager_instance = ItemManager()
    return _item_manager_instance