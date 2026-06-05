"""
资源文件工具 - 用于处理打包后的资源文件
"""

import os
import sys
import json
import shutil
from pathlib import Path


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径

    在打包为exe时，资源文件被打包在exe内部，需要通过sys._MEIPASS访问
    在开发环境中，直接使用相对路径

    Args:
        relative_path: 相对路径，如 "data/items.json"

    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹存储资源文件
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_user_data_path(filename):
    """
    获取用户数据文件的路径

    用户数据应该保存在用户目录下，而不是程序目录
    这样exe可以只读运行，用户数据可写

    Args:
        filename: 文件名，如 "users.json"

    Returns:
        用户数据文件的完整路径
    """
    # 获取用户目录
    if os.name == 'nt':  # Windows
        appdata_dir = os.getenv('APPDATA')
        user_dir = os.path.join(appdata_dir, '罪恶巷口')
    else:  # Linux/Mac
        home_dir = os.path.expanduser('~')
        user_dir = os.path.join(home_dir, '.罪恶巷口')

    # 创建目录（如果不存在）
    os.makedirs(user_dir, exist_ok=True)

    return os.path.join(user_dir, filename)


def copy_resource_to_user_data(resource_file, user_file=None):
    """
    将资源文件复制到用户数据目录

    用于首次运行或重置数据时

    Args:
        resource_file: 资源文件路径，如 "data/users.json"
        user_file: 用户数据文件名，如果为None则使用resource_file的文件名

    Returns:
        用户数据文件的路径
    """
    if user_file is None:
        user_file = os.path.basename(resource_file)

    user_path = get_user_data_path(user_file)
    resource_path = get_resource_path(resource_file)

    # 如果用户数据文件不存在，从资源复制
    if not os.path.exists(user_path) and os.path.exists(resource_path):
        try:
            shutil.copy2(resource_path, user_path)
            print(f"已创建用户数据文件: {user_path}")
        except Exception as e:
            print(f"复制资源文件失败: {e}")
            # 创建空文件
            with open(user_path, 'w', encoding='utf-8') as f:
                if user_file.endswith('.json'):
                    f.write('{}')

    return user_path


def load_json_resource(resource_file, default_data=None):
    """
    从资源文件加载JSON数据

    Args:
        resource_file: 资源文件路径
        default_data: 默认数据（如果文件不存在）

    Returns:
        JSON数据
    """
    if default_data is None:
        default_data = {}

    try:
        resource_path = get_resource_path(resource_file)
        if os.path.exists(resource_path):
            with open(resource_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载资源文件失败 {resource_file}: {e}")

    return default_data


def load_json_user_data(filename, default_data=None):
    """
    从用户数据文件加载JSON数据

    Args:
        filename: 用户数据文件名
        default_data: 默认数据（如果文件不存在）

    Returns:
        JSON数据
    """
    if default_data is None:
        default_data = {}

    user_path = get_user_data_path(filename)

    try:
        if os.path.exists(user_path):
            with open(user_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载用户数据失败 {filename}: {e}")

    return default_data


def save_json_user_data(filename, data):
    """
    保存JSON数据到用户数据文件

    Args:
        filename: 用户数据文件名
        data: 要保存的数据

    Returns:
        bool: 是否成功
    """
    user_path = get_user_data_path(filename)

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(user_path), exist_ok=True)

        # 保存数据
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存用户数据失败 {filename}: {e}")
        return False


def init_user_data():
    """初始化用户数据目录和文件"""
    # 创建用户数据目录
    user_dir = os.path.dirname(get_user_data_path("dummy.txt"))
    os.makedirs(user_dir, exist_ok=True)

    # 复制默认数据文件（如果不存在）
    copy_resource_to_user_data("data/users.dat")
    copy_resource_to_user_data("data/items.json")

    return user_dir


if __name__ == "__main__":
    # 测试代码
    print("资源工具测试:")
    print(f"资源路径示例: {get_resource_path('data/items.json')}")
    print(f"用户数据路径示例: {get_user_data_path('users.dat')}")

    # 初始化用户数据
    user_dir = init_user_data()
    print(f"用户数据目录: {user_dir}")