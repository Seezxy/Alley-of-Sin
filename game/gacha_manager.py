"""
抽奖系统管理模块
负责抽奖逻辑、概率计算和物品生成
"""

import random
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from game.constants import GACHA_PRICE, GACHA_TEN_PRICE, GACHA_PROBABILITIES, GACHA_POOLS
from game.item_manager import get_item_manager
from game.user_manager import get_user_manager
from game.inventory import get_inventory_manager


class GachaManager:
    """抽奖管理器"""

    def __init__(self):
        """初始化抽奖管理器"""
        self.item_manager = get_item_manager()
        self.user_manager = get_user_manager()
        self.inventory_manager = get_inventory_manager()

        # 加载所有物品
        self.all_items = self.item_manager.get_all_items()

        # 按类型和稀有度分类物品
        self._categorize_items()

    def _categorize_items(self):
        """按类型和稀有度分类物品"""
        self.items_by_type = {}
        self.items_by_rarity = {}

        for item_id, item_data in self.all_items.items():
            item_type = item_data.get("type")
            rarity = item_data.get("rarity")

            # 按类型分类
            if item_type not in self.items_by_type:
                self.items_by_type[item_type] = []
            self.items_by_type[item_type].append(item_id)

            # 按稀有度分类
            if rarity not in self.items_by_rarity:
                self.items_by_rarity[rarity] = []
            self.items_by_rarity[rarity].append(item_id)

    def get_pool_items(self, pool_type: str) -> List[str]:
        """
        获取指定抽奖池的物品ID列表

        Args:
            pool_type: 抽奖池类型 (weapon/armor/accessory/all)

        Returns:
            物品ID列表
        """
        if pool_type == "all":
            # 返回所有物品
            return list(self.all_items.keys())
        return self.items_by_type.get(pool_type, [])

    def get_rarity_probability(self, rarity: str) -> float:
        """
        获取指定稀有度的概率

        Args:
            rarity: 稀有度

        Returns:
            概率值 (0-100)
        """
        return GACHA_PROBABILITIES.get(rarity, 0.0)

    def draw_rarity(self) -> str:
        """
        根据概率抽取稀有度

        Returns:
            稀有度字符串
        """
        rand = random.random() * 100  # 0-100之间的随机数

        cumulative = 0
        for rarity, prob in GACHA_PROBABILITIES.items():
            cumulative += prob
            if rand <= cumulative:
                return rarity

        # 如果由于浮点数精度问题没有返回，返回普通
        return "common"

    def draw_item(self, pool_type: str) -> Optional[Dict[str, Any]]:
        """
        从指定抽奖池抽取一个物品

        Args:
            pool_type: 抽奖池类型

        Returns:
            物品数据字典，如果失败返回None
        """
        # 获取抽奖池物品
        pool_items = self.get_pool_items(pool_type)
        if not pool_items:
            return None

        # 抽取稀有度
        rarity = self.draw_rarity()

        # 获取该稀有度的物品
        rarity_items = [item_id for item_id in pool_items
                       if self.all_items[item_id].get("rarity") == rarity]

        # 如果该稀有度没有物品，降级到下一个稀有度
        if not rarity_items:
            # 按稀有度排序
            rarities = list(GACHA_PROBABILITIES.keys())
            try:
                rarity_index = rarities.index(rarity)
                # 尝试更低的稀有度
                for lower_rarity in rarities[rarity_index+1:]:
                    lower_items = [item_id for item_id in pool_items
                                  if self.all_items[item_id].get("rarity") == lower_rarity]
                    if lower_items:
                        rarity_items = lower_items
                        rarity = lower_rarity
                        break
            except ValueError:
                pass

        # 如果还是没有物品，返回池中任意物品
        if not rarity_items:
            rarity_items = pool_items
            if pool_items:
                rarity = self.all_items[pool_items[0]].get("rarity", "common")

        # 随机选择一个物品
        if rarity_items:
            item_id = random.choice(rarity_items)
            return self.all_items[item_id]

        return None

    def draw_multiple(self, pool_type: str, count: int) -> List[Dict[str, Any]]:
        """
        从指定抽奖池抽取多个物品

        Args:
            pool_type: 抽奖池类型
            count: 抽取数量

        Returns:
            物品数据字典列表
        """
        results = []
        for _ in range(count):
            item = self.draw_item(pool_type)
            if item:
                results.append(item)
        return results

    def can_afford_single(self) -> bool:
        """
        检查是否可以支付单抽

        Returns:
            是否可以支付
        """
        return self.user_manager.has_enough_currency(GACHA_PRICE)

    def can_afford_ten(self) -> bool:
        """
        检查是否可以支付十连抽

        Returns:
            是否可以支付
        """
        return self.user_manager.has_enough_currency(GACHA_TEN_PRICE)

    def can_afford_hundred(self) -> bool:
        """
        检查是否可以支付百连抽

        Returns:
            是否可以支付
        """
        from game.constants import GACHA_HUNDRED_PRICE
        return self.user_manager.has_enough_currency(GACHA_HUNDRED_PRICE)

    def get_max_draws(self) -> int:
        """
        获取最大可抽次数（尽数抽）

        Returns:
            最大可抽次数
        """
        currency = self.user_manager.get_currency()
        return currency // GACHA_PRICE

    def perform_single_draw(self, pool_type: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        执行单抽

        Args:
            pool_type: 抽奖池类型

        Returns:
            (是否成功, 物品数据, 消息)
        """
        # 检查货币
        if not self.can_afford_single():
            return False, None, "货币不足，无法抽奖"

        # 扣除货币（不保存）
        if not self.user_manager.deduct_currency(GACHA_PRICE, save=False):
            return False, None, "扣除货币失败"

        # 抽取物品
        item_data = self.draw_item(pool_type)
        if not item_data:
            self.user_manager.add_currency(GACHA_PRICE, save=True)
            return False, None, "抽奖失败，未获得物品"

        # 创建物品实例并添加到背包（不保存）
        success = self.inventory_manager.add_item_to_inventory(item_data["id"], save=False)
        if not success:
            # 如果添加失败，返还货币
            self.user_manager.add_currency(GACHA_PRICE, save=True)
            return False, None, "添加物品到背包失败"

        self.user_manager.save_data()
        return True, item_data, "抽奖成功！"

    def perform_ten_draw(self, pool_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        执行十连抽

        Args:
            pool_type: 抽奖池类型

        Returns:
            (是否成功, 物品数据列表, 消息)
        """
        # 检查货币
        if not self.can_afford_ten():
            return False, [], "货币不足，无法进行十连抽"

        # 扣除货币（不保存）
        if not self.user_manager.deduct_currency(GACHA_TEN_PRICE, save=False):
            return False, [], "扣除货币失败"

        # 抽取10个物品
        items_data = self.draw_multiple(pool_type, 10)
        if not items_data:
            self.user_manager.add_currency(GACHA_TEN_PRICE, save=True)
            return False, [], "抽奖失败，未获得任何物品"

        # 创建物品实例并添加到背包（不保存）
        success_count = 0
        successful_items = []

        for item_data in items_data:
            success = self.inventory_manager.add_item_to_inventory(item_data["id"], save=False)
            if success:
                success_count += 1
                successful_items.append(item_data)

        if success_count == 0:
            self.user_manager.add_currency(GACHA_TEN_PRICE, save=True)
            return False, [], "添加物品到背包全部失败"

        self.user_manager.save_data()
        actual_items = successful_items if success_count == 10 else items_data[:success_count]
        return True, actual_items, f"十连抽成功！获得 {success_count} 个物品"

    def perform_hundred_draw(self, pool_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        执行百连抽

        Args:
            pool_type: 抽奖池类型

        Returns:
            (是否成功, 物品数据列表, 消息)
        """
        from game.constants import GACHA_HUNDRED_PRICE

        # 检查货币
        if not self.can_afford_hundred():
            return False, [], "货币不足，无法进行百连抽"

        # 扣除货币（不保存）
        if not self.user_manager.deduct_currency(GACHA_HUNDRED_PRICE, save=False):
            return False, [], "扣除货币失败"

        # 抽取100个物品
        items_data = self.draw_multiple(pool_type, 100)
        if not items_data:
            self.user_manager.add_currency(GACHA_HUNDRED_PRICE, save=True)
            return False, [], "抽奖失败，未获得任何物品"

        # 创建物品实例并添加到背包（不保存）
        success_count = 0
        successful_items = []

        for item_data in items_data:
            success = self.inventory_manager.add_item_to_inventory(item_data["id"], save=False)
            if success:
                success_count += 1
                successful_items.append(item_data)

        if success_count == 0:
            self.user_manager.add_currency(GACHA_HUNDRED_PRICE, save=True)
            return False, [], "添加物品到背包全部失败"

        self.user_manager.save_data()
        actual_items = successful_items if success_count == 100 else items_data[:success_count]
        return True, actual_items, f"百连抽成功！获得 {success_count} 个物品"

    def perform_max_draw(self, pool_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        执行尽数抽（有多少抽多少）

        Args:
            pool_type: 抽奖池类型

        Returns:
            (是否成功, 物品数据列表, 消息)
        """
        # 计算最大可抽次数
        max_draws = self.get_max_draws()
        if max_draws <= 0:
            return False, [], "货币不足，无法抽奖"

        total_cost = max_draws * GACHA_PRICE

        # 扣除货币（不保存）
        if not self.user_manager.deduct_currency(total_cost, save=False):
            return False, [], "扣除货币失败"

        # 抽取物品
        items_data = self.draw_multiple(pool_type, max_draws)
        if not items_data:
            self.user_manager.add_currency(total_cost, save=True)
            return False, [], "抽奖失败，未获得任何物品"

        # 创建物品实例并添加到背包（不保存）
        success_count = 0
        successful_items = []

        for item_data in items_data:
            success = self.inventory_manager.add_item_to_inventory(item_data["id"], save=False)
            if success:
                success_count += 1
                successful_items.append(item_data)

        if success_count == 0:
            self.user_manager.add_currency(total_cost, save=True)
            return False, [], "添加物品到背包全部失败"

        self.user_manager.save_data()
        actual_items = successful_items if success_count == max_draws else items_data[:success_count]
        return True, actual_items, f"尽数抽成功！消耗 {total_cost} 钞票，获得 {success_count} 个物品"

    def get_pool_statistics(self, pool_type: str) -> Dict[str, Any]:
        """
        获取抽奖池统计信息

        Args:
            pool_type: 抽奖池类型

        Returns:
            统计信息字典
        """
        pool_items = self.get_pool_items(pool_type)

        # 统计各稀有度数量
        rarity_counts = {}
        for rarity in GACHA_PROBABILITIES.keys():
            rarity_counts[rarity] = 0

        for item_id in pool_items:
            item_data = self.all_items.get(item_id)
            if item_data:
                rarity = item_data.get("rarity")
                if rarity in rarity_counts:
                    rarity_counts[rarity] += 1

        # 计算总数量
        total_items = len(pool_items)

        # 计算各稀有度百分比
        rarity_percentages = {}
        for rarity, count in rarity_counts.items():
            if total_items > 0:
                percentage = (count / total_items) * 100
            else:
                percentage = 0
            rarity_percentages[rarity] = round(percentage, 2)

        return {
            "total_items": total_items,
            "rarity_counts": rarity_counts,
            "rarity_percentages": rarity_percentages,
            "probabilities": GACHA_PROBABILITIES
        }

    def get_all_items_statistics(self) -> Dict[str, Any]:
        """
        获取所有装备的统计信息

        Returns:
            统计信息字典
        """
        # 统计各稀有度数量
        rarity_counts = {}
        for rarity in GACHA_PROBABILITIES.keys():
            rarity_counts[rarity] = 0

        # 按类型统计
        type_counts = {
            "weapon": 0,
            "armor": 0,
            "accessory": 0
        }

        for item_id, item_data in self.all_items.items():
            rarity = item_data.get("rarity")
            item_type = item_data.get("type")

            if rarity in rarity_counts:
                rarity_counts[rarity] += 1

            if item_type in type_counts:
                type_counts[item_type] += 1

        # 计算总数量
        total_items = len(self.all_items)

        # 计算各稀有度百分比
        rarity_percentages = {}
        for rarity, count in rarity_counts.items():
            if total_items > 0:
                percentage = (count / total_items) * 100
            else:
                percentage = 0
            rarity_percentages[rarity] = round(percentage, 2)

        # 计算各类型百分比
        type_percentages = {}
        for item_type, count in type_counts.items():
            if total_items > 0:
                percentage = (count / total_items) * 100
            else:
                percentage = 0
            type_percentages[item_type] = round(percentage, 2)

        return {
            "total_items": total_items,
            "rarity_counts": rarity_counts,
            "rarity_percentages": rarity_percentages,
            "type_counts": type_counts,
            "type_percentages": type_percentages,
            "all_items": self.all_items  # 包含所有装备数据
        }

    def get_user_gacha_history(self) -> List[Dict[str, Any]]:
        """
        获取用户抽奖历史（简化版，实际项目中可以保存到数据库）

        Returns:
            抽奖历史列表
        """
        # 这里返回空列表，实际项目中可以从数据库加载
        return []


# 单例实例
_gacha_manager_instance = None

def get_gacha_manager() -> GachaManager:
    """获取抽奖管理器单例实例"""
    global _gacha_manager_instance
    if _gacha_manager_instance is None:
        _gacha_manager_instance = GachaManager()
    return _gacha_manager_instance