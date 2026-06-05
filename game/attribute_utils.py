"""
属性工具类
提供统一的属性验证、边界检查和格式化功能
"""

from typing import Dict, Any


class AttributeUtils:
    """属性工具类，提供统一的属性验证、边界检查和格式化功能"""

    # 属性显示名称映射
    ATTRIBUTE_DISPLAY_NAMES = {
        'max_hp': '最大生命值',
        'damage_bonus': '伤害加成',
        'crit_rate': '暴击率',
        'crit_damage': '暴击伤害',
        'lifesteal': '生命偷取',
        'damage_reduction': '伤害减免',
        'dodge_chance': '闪避几率'
    }

    @staticmethod
    def clamp_attribute(attr_name: str, value: float) -> float:
        """
        将属性值限制在合理范围内，禁止负数

        Args:
            attr_name: 属性名称
            value: 属性值

        Returns:
            限制后的属性值
        """
        # 禁止所有属性为负数
        if value < 0:
            return 0.0

        # 特殊属性的上限检查
        if attr_name in ["crit_rate", "lifesteal", "dodge_chance"]:
            return min(value, 1.0)  # 百分比属性上限100%
        elif attr_name == "damage_reduction":
            return min(value, 0.99)  # 免伤上限99%

        return value

    @staticmethod
    def format_attribute(attr_name: str, value: float) -> str:
        """
        格式化属性值显示，正确处理正负值

        Args:
            attr_name: 属性名称
            value: 属性值

        Returns:
            格式化后的属性字符串
        """
        if value == 0:
            return "0"  # 0值不显示符号

        if attr_name == "max_hp":
            # max_hp显示为整数，带正号
            return f"+{value:.0f}"
        else:
            # 百分比属性显示为百分比，带正号
            return f"+{value*100:.1f}%"

    @staticmethod
    def safe_add_attributes(attr1: Dict[str, float], attr2: Dict[str, float]) -> Dict[str, float]:
        """
        安全地累加两个属性字典，应用边界检查

        Args:
            attr1: 第一个属性字典
            attr2: 第二个属性字典

        Returns:
            累加并限制后的属性字典
        """
        result = attr1.copy()

        for attr_name, value in attr2.items():
            if attr_name in result:
                result[attr_name] += value
            else:
                result[attr_name] = value

            # 应用边界检查，禁止负数
            result[attr_name] = AttributeUtils.clamp_attribute(attr_name, result[attr_name])

        return result

    @staticmethod
    def validate_and_fix_attributes(attributes: Dict[str, float]) -> Dict[str, float]:
        """
        验证并修复属性字典，确保所有属性值合法

        Args:
            attributes: 原始属性字典

        Returns:
            修复后的属性字典
        """
        result = {}

        for attr_name, value in attributes.items():
            # 应用边界检查，禁止负数
            result[attr_name] = AttributeUtils.clamp_attribute(attr_name, value)

        return result

    @staticmethod
    def get_attribute_display_name(attr_name: str) -> str:
        """
        获取属性的显示名称

        Args:
            attr_name: 属性名称

        Returns:
            显示名称
        """
        return AttributeUtils.ATTRIBUTE_DISPLAY_NAMES.get(attr_name, attr_name)

    @staticmethod
    def format_attribute_for_display(attr_name: str, attr_value: float) -> str:
        """
        格式化属性用于显示（名称 + 值）

        Args:
            attr_name: 属性名称
            attr_value: 属性值

        Returns:
            格式化后的字符串
        """
        display_name = AttributeUtils.get_attribute_display_name(attr_name)
        formatted_value = AttributeUtils.format_attribute(attr_name, attr_value)
        return f"{display_name}: {formatted_value}"


# 单例实例
_attribute_utils_instance = None

def get_attribute_utils() -> AttributeUtils:
    """获取属性工具类单例实例"""
    global _attribute_utils_instance
    if _attribute_utils_instance is None:
        _attribute_utils_instance = AttributeUtils()
    return _attribute_utils_instance