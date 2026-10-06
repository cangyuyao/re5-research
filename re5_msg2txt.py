import csv
import struct
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("用法: python script.py <msg文件路径>")
        return

    msg_file = sys.argv[1]
    text_output = os.path.splitext(msg_file)[0] + '.txt'
    
    tbl_input = 'font00_j.tbl'
    tbl_output = 'font00_j.tbl'

    # 1. 读取临时码表，建立映射
    id_to_char = {}
    id_to_width = {}
    
    try:
        with open(tbl_input, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                char_id = int(row['ID'])
                id_to_char[char_id] = row['Char']
                id_to_width[char_id] = row['Width']
    except FileNotFoundError:
        print(f"找不到临时码表 {tbl_input}，请检查路径。")
        return

    # 2. 解析游戏文本，更新宽度并按指定格式导出
    extracted_text = []
    current_line_chars = []
    line_index = 0
    
    try:
        with open(msg_file, 'rb') as f:
            f.seek(0x40)  # 跳过 0x40 之前的文件头指针区
            
            while True:
                chunk = f.read(4)
                if len(chunk) < 4:
                    # 处理文件末尾可能没有结束符的情况
                    if current_line_chars:
                        block = f"[Line {line_index}]\n{''.join(current_line_chars)}\n\n"
                        extracted_text.append(block)
                    break
                    
                char_id, char_width = struct.unpack('<HH', chunk)
                
                # {0,1025} 代表该句台词结束
                if char_id == 0 and char_width == 1025:
                    block = f"[Line {line_index}]\n{''.join(current_line_chars)}\n\n"
                    extracted_text.append(block)
                    line_index += 1
                    current_line_chars = []  # 清空缓冲，准备读取下一行
                else:
                    # 宽度大于 144 视为控制符
                    if char_width > 144:
                        if char_id == 0 and char_width == 1027:
                            current_line_chars.append('\n')  # 将 {0,1027} 直接转换为真实换行符
                        else:
                            current_line_chars.append(f"{{{char_id},{char_width}}}")
                    else:
                        if char_id in id_to_char:
                            current_line_chars.append(id_to_char[char_id])
                            id_to_width[char_id] = char_width
                        else:
                            current_line_chars.append(f"[UNK_ID:{char_id}]")
    except FileNotFoundError:
        print(f"找不到文件 {msg_file}，请检查路径。")
        return

    # 3. 写入导出的文本文件
    with open(text_output, 'w', encoding='utf-8') as f:
        # 去除末尾多余的空行，保证文件整洁
        f.write("".join(extracted_text).strip() + "\n")
    print(f"文本已成功导出至：{text_output}")

    # 4. 生成包含 Width 的完整码表
    with open(tbl_output, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Char', 'ID', 'Width'])
        for char_id, char in id_to_char.items():
            writer.writerow([char, char_id, id_to_width[char_id]])
    print(f"完整码表已生成至：{tbl_output}")

if __name__ == '__main__':
    main()