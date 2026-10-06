import os
import re

# ==========================================
# 配置区
# ==========================================
TARGET_DIR = r"Image\Archive\Msg2Resource_ej\etc\message"  # 包含 txt 文件的实际文件夹路径
MAX_LINES = 4                    # 允许的最大行数
# ==========================================

def check_text_blocks(directory_path):
    if not os.path.exists(directory_path):
        print(f"错误: 找不到路径 '{directory_path}'")
        return

    found_issues = False
    processed_files = 0

    for filename in os.listdir(directory_path):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(directory_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"读取文件失败 (编码错误): {filename}")
            continue

        processed_files += 1

        # 使用正则匹配 [Line XXX] 及其下方的文本块
        # (?=\n\n\[Line|\Z) 表示匹配到下一个 [Line 开头或文件末尾为止
        blocks = re.findall(r'\[Line (\d+)\]\n(.*?)(?=\n\n\[Line|\Z)', content, re.DOTALL)

        for line_id, text in blocks:
            # 去除首尾的空白字符（防止多余的空行干扰判断）
            clean_text = text.strip()
            if not clean_text:
                continue
            
            # 计算总行数： 基础1行 + 物理换行数量 + {0,1027}标签数量
            newline_count = clean_text.count('\n')
            separator_count = clean_text.count('{0,1027}')
            total_lines = 1 + newline_count + separator_count

            if total_lines > MAX_LINES:
                found_issues = True
                print(f"文件: {filename} | [Line {line_id}] | 实际行数: {total_lines}")
                print("-" * 50)
                print(clean_text)
                print("=" * 50 + "\n")

    print(f"扫描完成。共处理 {processed_files} 个文件。")
    if not found_issues:
        print("未发现超过 4 行的文本块。")

if __name__ == '__main__':
    check_text_blocks(TARGET_DIR)