#!/usr/bin/env python3
"""
生成小偷角色占位头像图片
需要安装：pip install Pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

def generate_thief_avatar():
    # 图片尺寸
    width, height = 120, 160

    # 创建新图片（深紫色主题）
    img = Image.new('RGB', (width, height), color=(44, 33, 55))  # 深紫色背景
    draw = ImageDraw.Draw(img)

    # 绘制简单边框
    draw.rectangle([5, 5, width-5, height-5], outline=(155, 89, 182), width=2)  # 紫色边框

    # 绘制小偷符号（简单轮廓）
    # 绘制帽子（类似兜帽）
    draw.polygon([(30, 30), (90, 30), (80, 60), (40, 60)], fill=(75, 54, 97))

    # 绘制面部轮廓
    draw.ellipse([40, 70, 80, 110], fill=(200, 182, 220), outline=(155, 89, 182))

    # 绘制眼睛（两个点）
    draw.ellipse([50, 85, 55, 90], fill=(44, 33, 55))  # 左眼
    draw.ellipse([65, 85, 70, 90], fill=(44, 33, 55))  # 右眼

    # 绘制嘴（微笑）
    draw.arc([50, 100, 70, 110], start=0, end=180, fill=(155, 89, 182), width=2)

    # 添加文字"小偷"
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("msyh.ttc", 20)  # 微软雅黑
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 20)  # Arial
        except:
            font = ImageFont.load_default()

    # 绘制文字
    text = "小偷"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = height - 30
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

    # 保存图片
    output_path = "images/char_thief.png"
    img.save(output_path, "PNG")
    print(f"已生成占位头像: {output_path}")
    print(f"尺寸: {width}×{height} 像素")

    # 同时创建TXT描述文件（保持与其他角色一致）
    txt_path = "images/char_thief.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("小偷角色占位头像\n")
        f.write("后续可替换为定制图片\n")
    print(f"已创建描述文件: {txt_path}")

if __name__ == "__main__":
    # 确保images目录存在
    if not os.path.exists("images"):
        os.makedirs("images")

    try:
        generate_thief_avatar()
        print("\n使用说明：")
        print("1. 运行游戏测试角色: python main.py")
        print("2. 如需更换头像，直接替换 images/char_thief.png 文件")
        print("3. 建议使用120×160像素的PNG格式图片")
    except ImportError:
        print("错误: 需要安装Pillow库")
        print("请运行: pip install Pillow")
        exit(1)
    except Exception as e:
        print(f"生成图片时出错: {e}")
        exit(1)