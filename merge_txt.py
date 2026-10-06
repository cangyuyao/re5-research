import sys
import os
import re

# ==========================================
# 默认配置区 (可按需修改，双击运行时将读取这里的配置)
# ==========================================
# 注意: Windows 路径前面最好加上 r，防止 \ 符号被当成转义字符导致报错
DEFAULT_EN_DIR = r"Image\Archive\Msg2Resource_e\etc\message"   # 英文 txt 文件夹路径
DEFAULT_JP_DIR = r"Image\Archive\Msg2Resource_j\etc\message"   # 日文 txt 文件夹路径
DEFAULT_OUT_DIR = r"Image\Archive\Msg2Resource_ej\etc\message" # 合并后的 txt 输出文件夹路径

# 文本修饰标签配置
EN_PREFIX = "{0,1042}{20,1042}{20,1042}"             # 英文文本前缀
EN_SUFFIX = ""                                             # 英文文本后缀
JP_PREFIX = ""                                             # 日文文本前缀
JP_SUFFIX = ""                                             # 日文文本后缀
MERGE_SEPARATOR = "{0,1027}"                               # 英日双语合并时的分隔符
# ==========================================

def parse_msg_txt(filepath):
    """解析导出的 txt 文件，返回 {line_index: text_content} 的字典"""
    data = {}
    if not os.path.exists(filepath):
        return data

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则匹配 [Line X] 及其下方的文本块
    blocks = re.findall(r'\[Line (\d+)\]\n(.*?)(?=\n\n\[Line|\Z)', content, re.DOTALL)
    for idx_str, text in blocks:
        data[int(idx_str)] = text.strip()
    return data

def insert_tags_smartly(text, prefix, suffix):
    """智能插入标签：将修饰标签放在游戏自带控制标签的内部，避免破坏语音或时间轴"""
    if not text:
        return text
        
    # 正则表达式匹配游戏自带的控制标签，例如 {1,255} 或 <WAIT> 等
    # 匹配开头的控制标签
    leading_match = re.match(r'^(?:\{[0-9]+,[0-9]+\}|<[^>]+>)+', text)
    leading_tags = leading_match.group(0) if leading_match else ""
    
    # 截取掉开头的标签后的剩余部分
    remaining_text = text[len(leading_tags):]
    
    # 匹配结尾的控制标签
    trailing_search = re.search(r'(?:\{[0-9]+,[0-9]+\}|<[^>]+>)+$', remaining_text)
    trailing_tags = trailing_search.group(0) if trailing_search else ""
    
    # 提取真正的可见纯文本
    if trailing_tags:
        actual_text = remaining_text[:-len(trailing_tags)]
    else:
        actual_text = remaining_text
        
    # 如果这行文本完全由控制标签组成（没有实际文字），则不插入修饰标签
    if not actual_text:
        return text
        
    # 将我们的修饰标签紧贴在真实文本的两侧，将原版控制标签顶在最外层
    return f"{leading_tags}{prefix}{actual_text}{suffix}{trailing_tags}"

def wrap_en_text(text):
    """为英文文本智能添加修饰标签"""
    return insert_tags_smartly(text, EN_PREFIX, EN_SUFFIX)

def wrap_jp_text(text):
    """为日文文本智能添加修饰标签"""
    return insert_tags_smartly(text, JP_PREFIX, JP_SUFFIX)

def main():
    # 优先读取命令行参数，如果没有传参则使用上方的全局默认配置
    en_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EN_DIR
    jp_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_JP_DIR
    out_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT_DIR
    
    if not os.path.exists(en_dir):
        print(f"错误: 找不到英文 txt 文件夹 '{en_dir}'")
        return
        
    if not os.path.exists(jp_dir):
        print(f"错误: 找不到日文 txt 文件夹 '{jp_dir}'")
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # 遍历英文文件夹中的所有 txt 文件
    processed_count = 0
    for en_filename in os.listdir(en_dir):
        if not en_filename.endswith('.txt'):
            continue
            
        # 提取基础文件名，假设格式为 xxx_e.txt，提取出 xxx
        base_name = en_filename
        if base_name.endswith('_e.txt'):
            base_name = base_name.replace('_e.txt', '')
        elif base_name.endswith('.txt'):
            base_name = base_name[:-4]
            
        jp_filename = f"{base_name}_j.txt"
        out_filename = f"{base_name}_j.txt"
        
        en_txt_file = os.path.join(en_dir, en_filename)
        jp_txt_file = os.path.join(jp_dir, jp_filename)
        out_txt_file = os.path.join(out_dir, out_filename)

        if not os.path.exists(jp_txt_file):
            print(f"跳过: 找不到对应的日文文件 {jp_txt_file}")
            continue

        en_data = parse_msg_txt(en_txt_file)
        jp_data = parse_msg_txt(jp_txt_file)

        # 获取所有行号并排序，确保不会漏掉仅存在于某一语言中的行
        all_lines = sorted(set(en_data.keys()).union(set(jp_data.keys())))

        merged_output = []
        for line_idx in all_lines:
            en_text = en_data.get(line_idx, "")
            jp_text = jp_data.get(line_idx, "")
            
            if en_text and jp_text:
                if en_text == jp_text:
                    # 如果英文和日文内容完全一致，将其视为最终文本，只加日文标签（单层）避免冗余
                    merged_text = wrap_jp_text(jp_text)
                else:
                    merged_text = f"{wrap_en_text(en_text)}{MERGE_SEPARATOR}{wrap_jp_text(jp_text)}"
            elif en_text:
                # 只有英文的情况
                merged_text = wrap_en_text(en_text)
            elif jp_text:
                # 只有日文的情况
                merged_text = wrap_jp_text(jp_text)
            else:
                merged_text = ""

            merged_output.append(f"[Line {line_idx}]\n{merged_text}\n")

        with open(out_txt_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(merged_output))
        
        print(f"已合并: {out_filename}")
        processed_count += 1

    print(f"\n批量合并完成，共处理 {processed_count} 个文件。")
    print(f"所有文件已保存至: {out_dir}")

if __name__ == '__main__':
    main()