"""
熔炼系统管理类
负责装备熔炼和合成逻辑
"""
import random
from typing import Dict, List, Optional, Tuple
from game.item_manager import get_item_manager
from game.inventory import get_inventory_manager


class SmeltingManager:
    """熔炼管理器"""

    def __init__(self):
        self.item_manager = get_item_manager()
        self.inventory_manager = get_inventory_manager()

        # 稀有度升级顺序
        self.rarity_order = ["common", "uncommon", "rare", "epic", "legendary", "mythical"]

        # 熔炼配置
        self.smelting_config = {
            "base_cost": 100,  # 基础需要100件装备
            "random_discount": 0.8,  # 随机类别打八折，需要80件
            "max_rarity": "mythical"  # 最高合成到神话
        }

        # 装备类型映射
        self.equipment_types = ["weapon", "armor", "accessory"]

        # 缓存：上次计算的背包数量
        self._counts_cache = None
        self._counts_cache_inventory_size = -1

    def _compute_inventory_counts(self) -> Dict[tuple, int]:
        """单次遍历背包，预计算各(稀有度, 类型)的物品数量"""
        inventory_items = self.inventory_manager.get_inventory_items()
        current_size = len(inventory_items)

        # 如果背包大小没变，使用缓存
        if self._counts_cache is not None and self._counts_cache_inventory_size == current_size:
            return self._counts_cache

        counts = {}
        for item in inventory_items:
            if item.get("equipped", False):
                continue
            item_type = item.get("item_type", "")
            if item_type not in self.equipment_types:
                continue
            rarity = item.get("rarity", "common")
            key = (rarity, item_type)
            counts[key] = counts.get(key, 0) + 1

        self._counts_cache = counts
        self._counts_cache_inventory_size = current_size
        return counts

    def invalidate_counts_cache(self):
        """使数量缓存失效（背包变化后调用）"""
        self._counts_cache = None
        self._counts_cache_inventory_size = -1

    def get_available_count(self, target_rarity: str, target_type: str = None) -> int:
        """快速获取可用物品数量（使用缓存，只做字典查找）"""
        counts = self._compute_inventory_counts()
        if target_type:
            return counts.get((target_rarity, target_type), 0)
        else:
            return sum(v for (r, _t), v in counts.items() if r == target_rarity)

    def get_next_rarity(self, current_rarity: str) -> Optional[str]:
        """获取下一级稀有度"""
        try:
            current_index = self.rarity_order.index(current_rarity)
            if current_index < len(self.rarity_order) - 1:
                return self.rarity_order[current_index + 1]
        except ValueError:
            pass
        return None

    def get_smelting_cost(self, target_type: str, is_random: bool = False) -> int:
        """获取熔炼所需装备数量"""
        base_cost = self.smelting_config["base_cost"]
        if is_random:
            return int(base_cost * self.smelting_config["random_discount"])
        return base_cost

    def get_available_items_for_smelting(self, target_rarity: str, target_type: str = None) -> List[Dict]:
        """获取可用于熔炼的物品列表（仅在确认熔炼时调用，遍历所有物品）"""
        inventory_items = self.inventory_manager.get_inventory_items()
        available_items = []

        for item in inventory_items:
            if item.get("equipped", False):
                continue
            item_rarity = item.get("rarity", "common")
            item_type = item.get("item_type", "")
            if item_rarity != target_rarity:
                continue
            if target_type and item_type != target_type:
                continue
            if item_type not in self.equipment_types:
                continue
            available_items.append(item)

        return available_items

    def can_smelt(self, target_rarity: str, target_type: str = None, is_random: bool = False) -> Tuple[bool, str, List[str]]:
        """
        检查是否可以熔炼（使用缓存计数，不需要遍历背包）

        Returns:
            (是否可以熔炼, 错误消息, 可用的物品实例ID列表)
        """
        if target_rarity not in self.rarity_order:
            return False, f"无效的稀有度: {target_rarity}", []
        if target_rarity == self.smelting_config["max_rarity"]:
            return False, "已经是最高稀有度，无法继续合成", []

        required_count = self.get_smelting_cost(target_type, is_random)
        available_count = self.get_available_count(target_rarity, target_type)

        if available_count < required_count:
            if target_type:
                return False, f"需要{required_count}件{target_type}类型的{target_rarity}装备，当前只有{available_count}件", []
            else:
                return False, f"需要{required_count}件{target_rarity}装备，当前只有{available_count}件", []

        # 仅当确认可以熔炼时才获取实际物品列表
        available_items = self.get_available_items_for_smelting(target_rarity, target_type)
        instance_ids = [item["instance_id"] for item in available_items[:required_count]]
        return True, "", instance_ids

    def get_random_item_of_next_rarity(self, current_rarity: str, item_type: str = None) -> Optional[Dict]:
        """随机获取下一稀有度的物品"""
        next_rarity = self.get_next_rarity(current_rarity)
        if not next_rarity:
            return None

        all_items = self.item_manager.get_all_items()
        candidate_items = []

        for item_id, item_def in all_items.items():
            if item_def.get("rarity") == next_rarity:
                if item_type and item_def.get("type") != item_type:
                    continue
                candidate_items.append(item_def)

        if not candidate_items:
            return None

        return random.choice(candidate_items)

    def smelt_items(self, target_rarity: str, target_type: str = None, is_random: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """执行单次熔炼（兼容旧接口）"""
        success, msg, results = self.smelt_multiple(target_rarity, target_type, is_random, 1)
        if success and results:
            return True, msg, results[0]
        return success, msg, None

    def smelt_multiple(self, target_rarity: str, target_type: str = None, is_random: bool = False,
                       count: int = 1) -> Tuple[bool, str, List[Dict]]:
        """
        执行多次熔炼

        Returns:
            (是否成功, 消息, 合成物品列表)
        """
        if count < 1:
            return False, "熔炼次数必须大于0", []

        required_per_time = self.get_smelting_cost(target_type, is_random)
        total_required = required_per_time * count

        # 检查可用数量
        available_count = self.get_available_count(target_rarity, target_type)
        if available_count < total_required:
            max_possible = available_count // required_per_time
            return False, f"材料不足！需要{total_required}件，当前可用{available_count}件（最多熔炼{max_possible}次）", []

        # 获取需要的物品实例ID
        available_items = self.get_available_items_for_smelting(target_rarity, target_type)
        consumed_ids = [item["instance_id"] for item in available_items[:total_required]]

        # 批量移除消耗物品（不保存）
        for instance_id in consumed_ids:
            self.inventory_manager.remove_item_from_inventory(instance_id, save=False)

        # 生成结果物品
        results = []
        for _ in range(count):
            result_item = self.get_random_item_of_next_rarity(target_rarity, target_type)
            if result_item:
                new_instance = self.item_manager.create_item_instance(result_item["id"])
                if new_instance:
                    new_instance["name"] = result_item["name"]
                    new_instance["rarity"] = result_item["rarity"]
                    new_instance["item_type"] = result_item["type"]
                    new_instance["description"] = result_item.get("description", "")
                    new_instance["attributes"] = result_item.get("attributes", {}).copy()
                    self.inventory_manager.add_item_to_inventory(new_instance, save=False)
                    results.append(result_item)

        from game.user_manager import get_user_manager
        get_user_manager().save_data()
        self.invalidate_counts_cache()

        if results:
            return True, f"熔炼{count}次成功！获得 {len(results)} 件装备", results
        else:
            return False, "熔炼失败，未获得装备", []

    def get_smelting_options(self) -> List[Dict]:
        """获取所有可用的熔炼选项（使用缓存计数，单次遍历）"""
        # 预计算所有计数
        counts = self._compute_inventory_counts()
        options = []

        for rarity in self.rarity_order:
            if rarity == self.smelting_config["max_rarity"]:
                continue

            next_rarity = self.get_next_rarity(rarity)
            if not next_rarity:
                continue

            for eq_type in self.equipment_types:
                required_count = self.get_smelting_cost(eq_type, False)
                available_count = counts.get((rarity, eq_type), 0)
                if available_count >= required_count:
                    options.append({
                        "current_rarity": rarity,
                        "next_rarity": next_rarity,
                        "type": eq_type,
                        "is_random": False,
                        "required_count": required_count,
                        "available_count": available_count,
                        "display_name": f"{eq_type} → {next_rarity}"
                    })

            # 随机类型选项
            required_count = self.get_smelting_cost(None, True)
            available_count = sum(v for (r, _t), v in counts.items() if r == rarity)
            if available_count >= required_count:
                options.append({
                    "current_rarity": rarity,
                    "next_rarity": next_rarity,
                    "type": "random",
                    "is_random": True,
                    "required_count": required_count,
                    "available_count": available_count,
                    "display_name": f"随机类型 → {next_rarity} (八折)"
                })

        return options

    def auto_select_items(self, target_rarity: str, target_type: str = None) -> List[str]:
        """自动选择用于熔炼的物品"""
        available_items = self.get_available_items_for_smelting(target_rarity, target_type)
        required_count = self.get_smelting_cost(target_type, target_type is None)
        return [item["instance_id"] for item in available_items[:required_count]]


# 单例实例
_smelting_manager_instance = None

def get_smelting_manager() -> SmeltingManager:
    """获取熔炼管理器单例实例"""
    global _smelting_manager_instance
    if _smelting_manager_instance is None:
        _smelting_manager_instance = SmeltingManager()
    return _smelting_manager_instance