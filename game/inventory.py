"""
背包管理模块
负责背包和装备的逻辑管理
"""
import uuid
from typing import Dict, List, Optional, Any
from game.item_manager import ItemManager
from game.user_manager import get_user_manager
from game.utils import get_pinyin_for_sort
from game.attribute_utils import get_attribute_utils


class InventoryManager:
    """背包管理器"""

    def __init__(self):
        """初始化背包管理器"""
        self.item_manager = ItemManager()
        self.user_manager = get_user_manager()

    def create_item_instance(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        创建物品实例（只存储最小化数据）

        Args:
            item_id: 物品ID

        Returns:
            物品实例数据，如果物品不存在则返回None
        """
        item_data = self.item_manager.get_item(item_id)
        if not item_data:
            return None

        # 创建物品实例 - 只存储必要信息
        instance_id = str(uuid.uuid4())
        item_instance = {
            "instance_id": instance_id,
            "item_id": item_id,  # 只存储代号
            "equipped": False,
            "created_at": None  # 可以在需要时添加时间戳
        }

        return item_instance

    def get_item_full_info(self, item_instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取物品的完整信息（动态加载）

        Args:
            item_instance: 物品实例数据（只包含最小化信息）

        Returns:
            包含完整信息的物品数据
        """
        item_id = item_instance.get("item_id")
        if not item_id:
            return item_instance.copy()

        # 从物品管理器获取完整信息
        item_data = self.item_manager.get_item(item_id)
        if not item_data:
            return item_instance.copy()

        # 合并信息
        full_item = item_instance.copy()
        full_item.update({
            "name": item_data["name"],
            "description": item_data["description"],
            "item_type": item_data.get("type", "unknown"),
            "rarity": item_data["rarity"],
            "attributes": item_data.get("attributes", {})
        })

        return full_item

    def add_item_to_inventory(self, item_id_or_instance: Any, save: bool = True) -> bool:
        """
        添加物品到背包

        Args:
            item_id_or_instance: 物品ID或完整的物品实例
            save: 是否立即保存到磁盘

        Returns:
            是否添加成功
        """
        if isinstance(item_id_or_instance, str):
            # 如果是物品ID，创建物品实例
            item_instance = self.create_item_instance(item_id_or_instance)
            if not item_instance:
                return False
        elif isinstance(item_id_or_instance, dict):
            # 如果是完整的物品实例，直接使用
            item_instance = item_id_or_instance
        else:
            return False

        # 添加到背包
        return self.user_manager.add_item_to_inventory(item_instance, save=save)

    def remove_item_from_inventory(self, instance_id: str, save: bool = True) -> bool:
        """
        从背包移除物品

        Args:
            instance_id: 物品实例ID
            save: 是否立即保存到磁盘

        Returns:
            是否移除成功
        """
        return self.user_manager.remove_item_from_inventory(instance_id, save=save)

    def equip_item(self, instance_id: str) -> bool:
        """
        装备物品

        Args:
            instance_id: 物品实例ID

        Returns:
            是否装备成功
        """
        # 获取物品信息（最小化数据）
        inventory_items = self.user_manager.get_inventory_items()
        target_item = None

        for item in inventory_items:
            if item.get("instance_id") == instance_id:
                target_item = item
                break

        if not target_item:
            return False

        # 获取物品完整信息以确定类型
        full_item = self.get_item_full_info(target_item)
        item_type = full_item.get("item_type")
        slot = self._get_equipment_slot(item_type)

        if not slot:
            return False

        # 装备物品
        return self.user_manager.equip_item(instance_id, slot)

    def unequip_item(self, slot: str) -> bool:
        """
        卸下装备

        Args:
            slot: 装备槽位

        Returns:
            是否卸下成功
        """
        return self.user_manager.unequip_item(slot)

    def get_inventory(self) -> Dict[str, Any]:
        """
        获取背包数据

        Returns:
            背包数据
        """
        return self.user_manager.get_inventory()

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """
        获取背包中的所有物品（动态加载完整信息）

        Returns:
            包含完整信息的物品列表
        """
        # 获取最小化的物品实例数据
        item_instances = self.user_manager.get_inventory_items()

        # 为每个物品加载完整信息
        full_items = []
        for item_instance in item_instances:
            full_item = self.get_item_full_info(item_instance)
            full_items.append(full_item)

        return full_items

    def get_equipped_items(self) -> Dict[str, Optional[Dict]]:
        """
        获取当前装备的物品（动态加载完整信息）

        Returns:
            装备槽位到物品详情的映射
        """
        # 获取装备数据（只包含instance_id）
        equipment = self.user_manager.get_equipment()
        inventory_items = self.user_manager.get_inventory_items()

        equipped_items = {}

        for slot, instance_id in equipment.items():
            if not instance_id:
                equipped_items[slot] = None
                continue

            # 在背包中查找对应的物品实例
            target_item = None
            for item_instance in inventory_items:
                if item_instance.get("instance_id") == instance_id:
                    target_item = item_instance
                    break

            if target_item:
                # 加载完整信息
                full_item = self.get_item_full_info(target_item)
                equipped_items[slot] = full_item
            else:
                equipped_items[slot] = None

        return equipped_items

    def get_equipment(self) -> Dict[str, Optional[str]]:
        """
        获取装备数据

        Returns:
            装备数据
        """
        return self.user_manager.get_equipment()

    def get_inventory_capacity(self) -> int:
        """
        获取背包容量

        Returns:
            背包容量
        """
        inventory = self.user_manager.get_inventory()
        return inventory.get("capacity", 20)

    def get_inventory_used(self) -> int:
        """
        获取已使用的背包格子数

        Returns:
            已使用的格子数
        """
        inventory = self.user_manager.get_inventory()
        items = inventory.get("items", [])
        return len(items)

    def get_inventory_free(self) -> int:
        """
        获取剩余的背包格子数

        Returns:
            剩余的格子数
        """
        capacity = self.get_inventory_capacity()
        used = self.get_inventory_used()
        return max(0, capacity - used)

    def get_filtered_sorted_items(self, filter_type: str = "all", sort_by: str = "rarity", search_text: str = None) -> List[Dict[str, Any]]:
        """
        获取筛选和排序后的物品列表

        Args:
            filter_type: 筛选类型 - "all", "weapon", "armor", "accessory"
            sort_by: 排序方式 - 只支持 "rarity"（按稀有度排序，稀有度相同按拼音排序）
            search_text: 搜索文本，用于名称模糊匹配

        Returns:
            筛选和排序后的物品列表
        """
        # 获取所有物品
        all_items = self.get_inventory_items()

        # 第一步：按类型筛选
        if filter_type == "all":
            filtered_items = all_items
        else:
            filtered_items = [item for item in all_items if item.get("item_type") == filter_type]

        # 第二步：按名称搜索（如果提供了搜索文本）
        if search_text:
            filtered_items = [item for item in filtered_items
                             if search_text in item.get("name", "").lower()]

        # 第三步：排序（先按稀有度排序，稀有度相同按拼音排序）
        # 按稀有度排序（神话→普通，稀有的在上面）
        # 注意：需要包含所有稀有度，包括"fine"
        rarity_order = {"mythical": 0, "legendary": 1, "epic": 2, "rare": 3,
                       "uncommon": 4, "fine": 5, "common": 6}

        # 多级排序：先按稀有度，再按拼音
        filtered_items.sort(key=lambda x: (
            rarity_order.get(x.get("rarity", "common"), 6),  # 稀有度排序
            get_pinyin_for_sort(x.get("name", ""))           # 拼音排序
        ))

        return filtered_items

    def can_add_item(self) -> bool:
        """
        检查是否可以添加物品

        Returns:
            是否可以添加
        """
        return self.get_inventory_free() > 0

    def get_item_attributes(self, instance_id: str) -> Dict[str, Any]:
        """
        获取物品属性

        Args:
            instance_id: 物品实例ID

        Returns:
            物品属性
        """
        inventory_items = self.user_manager.get_inventory_items()

        for item_instance in inventory_items:
            if item_instance.get("instance_id") == instance_id:
                # 加载完整信息以获取属性
                full_item = self.get_item_full_info(item_instance)
                return full_item.get("attributes", {})

        return {}

    def get_equipment_attributes(self) -> Dict[str, Any]:
        """
        获取所有装备的属性总和

        Returns:
            属性总和
        """
        equipped_items = self.get_equipped_items()
        total_attributes = {}
        attribute_utils = get_attribute_utils()

        for slot, item in equipped_items.items():
            if item:
                attributes = item.get("attributes", {})
                # 使用属性工具类安全累加属性
                total_attributes = attribute_utils.safe_add_attributes(total_attributes, attributes)

        return total_attributes

    def _get_equipment_slot(self, item_type: str) -> Optional[str]:
        """
        根据物品类型获取装备槽位

        Args:
            item_type: 物品类型

        Returns:
            装备槽位，如果不支持装备则返回None
        """
        equipment_slots = {
            "weapon": "weapon",
            "armor": "armor",
            "accessory": "accessory"
        }

        return equipment_slots.get(item_type)


# 单例实例
_inventory_manager_instance = None


def get_inventory_manager() -> InventoryManager:
    """获取背包管理器单例实例"""
    global _inventory_manager_instance
    if _inventory_manager_instance is None:
        _inventory_manager_instance = InventoryManager()
    return _inventory_manager_instance