import os
import csv
import re
from PIL import Image, ImageFont, ImageDraw

# ==========================================
# 默认路径与文件名配置区 (可按需修改)
# ==========================================
FONT_PATH = "Roboto-Regular.ttf"  # 字体文件路径
FONT_SIZE = 30                    # 测量的基准字号
MULTIPLIER = 4                    # 宽度的乘数

CONFIG_INPUT = "font00_j.tbl"     # 输入的字符与ID配置文件路径
TBL_OUTPUT = "font00_custom.tbl"  # 输出的自定义码表路径

INCLUDE_SIDE_BEARINGS = True      # True: 包含左右空白边距(排版宽度)；False: 仅计算纯文字墨迹宽度
COMPENSATE_WIDTH = 2.0            # 当 INCLUDE_SIDE_BEARINGS 为 False 时，额外增加的像素补偿值 (支持小数)
# ==========================================

# ==========================================
# 需要提取的字符范围配置区
# ==========================================
# 脚本只会从 CONFIG_INPUT 中提取以下指定的字符
CHAR_CONFIG = [
    "[0-9]", 
    "[A-Z]", 
    "[a-z]",
    " "
]
# ==========================================

def expand_char_config(config_list):
    """解析列表中的字符和范围，展开为一个字符集合"""
    chars = set()
    pattern = re.compile(r'\[(.)-(.)\]')
    
    for item in config_list:
        match = pattern.match(item)
        if match:
            start_char, end_char = match.groups()
            for codepoint in range(ord(start_char), ord(end_char) + 1):
                chars.add(chr(codepoint))
        else:
            for char in item:
                chars.add(char)
                
    return chars

def get_char_width(font, char, include_side_bearings):
    """测量单个字符的宽度，返回浮点数(精确到小数)"""
    if include_side_bearings:
        # 获取排版宽度 (Advance Width)，直接返回原生的高精度 float 值
        try:
            return float(font.getlength(char))
        except AttributeError:
            # 兼容极老版本的 Pillow
            return float(font.getsize(char)[0])
    else:
        # 【物理像素级测量】
        # 注意：物理像素边界天生是整数，但为了统一计算，这里也返回 float
        img = Image.new("L", (100, 100), 0)
        draw = ImageDraw.Draw(img)
        
        draw.text((20, 20), char, font=font, fill=255)
        bbox = img.getbbox()
        
        if bbox:
            # bbox = (left, top, right, bottom)
            return float(bbox[2] - bbox[0])
        else:
            # 如果画出来是空的（比如空格），退回使用默认排版宽度
            try:
                return float(font.getlength(char))
            except AttributeError:
                return float(font.getsize(char)[0])

def main():
    if not os.path.exists(FONT_PATH):
        print(f"错误: 找不到字体文件 '{FONT_PATH}'")
        return
        
    if not os.path.exists(CONFIG_INPUT):
        print(f"错误: 找不到字符配置文件 '{CONFIG_INPUT}'")
        return

    target_chars = expand_char_config(CHAR_CONFIG)
    
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        print(f"错误: 无法加载字体文件 '{FONT_PATH}'")
        return

    tbl_data = []
    processed_chars = set()
    
    with open(CONFIG_INPUT, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader):
            if not row or len(row) < 2:
                continue
                
            if row_idx == 0 and row[0].strip().lower() == 'char':
                continue
                
            char = row[0]
            try:
                char_id = int(row[1])
            except ValueError:
                continue
            
            if char in target_chars and char not in processed_chars:
                # 测量原始宽度 (得到带有小数的高精度浮点数)
                actual_width = get_char_width(font, char, INCLUDE_SIDE_BEARINGS)
                
                # 如果不包含排版边距，则加上设定的补偿值
                if not INCLUDE_SIDE_BEARINGS:
                    actual_width += COMPENSATE_WIDTH
                    
                # 核心修改：宽度 * 倍数后，再使用 round() 取整
                final_width = int(round(actual_width * MULTIPLIER))
                
                tbl_data.append({
                    'Char': char,
                    'ID': char_id,
                    'Width': final_width
                })
                processed_chars.add(char)

    missing_chars = target_chars - processed_chars
    if missing_chars:
        print(f"提示: 有 {len(missing_chars)} 个指定字符未在配置文件中找到 (如: {list(missing_chars)[:5]})")

    with open(TBL_OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Char', 'ID', 'Width'])
        writer.writeheader()
        writer.writerows(tbl_data)

    print(f"生成结束，共提取并输出了 {len(tbl_data)} 个字符数据。")
    print(f"Side Bearings: {INCLUDE_SIDE_BEARINGS}", end="")
    if not INCLUDE_SIDE_BEARINGS:
        print(f" (已附加补偿值: {COMPENSATE_WIDTH} 像素)")
    else:
        print()

if __name__ == '__main__':
    main()