import os
import csv
from PIL import Image, ImageFont, ImageDraw

# ==========================================
# 配置区
# ==========================================
FONT_PATH = "Roboto-Regular.ttf"  # 字体文件路径
FONT_SIZE = 30                    # 建议字号 
TBL_INPUT = "font00_j.tbl"        # 输入的字符表
OUTPUT_IMG = "font_texture.png"   # 输出的贴图文件名

CELL_SIZE = 36                    # 单个字符的网格边长 (px)
COLS = 64                         # 每行字符数 (紧凑排列)
# ==========================================

def main():
    if not os.path.exists(FONT_PATH):
        print(f"错误: 找不到字体文件 '{FONT_PATH}'")
        return
        
    if not os.path.exists(TBL_INPUT):
        print(f"错误: 找不到字符配置文件 '{TBL_INPUT}'")
        return

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        print(f"错误: 无法加载字体文件 '{FONT_PATH}'")
        return

    char_map = {}
    max_slot_index = -1
    
    # 1. 解析 tbl 文件获取字符与对应 ID
    with open(TBL_INPUT, 'r', encoding='utf-8-sig') as f:
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
            
            # 【关键修复】: 将双数 ID 转换为连续的真实槽位序号 (0, 1, 2, 3...)
            slot_index = char_id // 2
            
            char_map[slot_index] = char
            if slot_index > max_slot_index:
                max_slot_index = slot_index

    if not char_map:
        print("错误: 配置文件中没有读取到有效字符数据。")
        return

    # 2. 根据最大的连续槽位序号，计算贴图的行数和总高度
    rows = (max_slot_index // COLS) + 1
    img_width = COLS * CELL_SIZE
    img_height = rows * CELL_SIZE

    # 3. 创建纯透明背景画布 (RGBA)
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 4. 遍历所有收集到的字符并绘制到对应槽位
    for slot_index, char in char_map.items():
        col = slot_index % COLS
        row = slot_index // COLS
        
        # 计算该字符网格的左上角坐标
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        
        # 绘制纯白文字
        # anchor="la" (Left-Ascender) 确保包含左侧排版边距，且文字基线对齐
        draw.text((x, y), char, font=font, fill=(255, 255, 255, 255), anchor="la")

    # 5. 保存输出
    img.save(OUTPUT_IMG, "PNG")
    print(f"贴图生成完毕！")
    print(f"包含字符数: {len(char_map)}")
    print(f"贴图排版: 每行 {COLS} 个字符 (已将双数 ID 压缩映射为连续网格)")
    print(f"贴图尺寸: {img_width} x {img_height} px")
    print(f"输出文件: {OUTPUT_IMG}")

if __name__ == '__main__':
    main()