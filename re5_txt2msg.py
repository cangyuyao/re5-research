import csv
import struct
import sys
import os
import re

# ==========================================
# 默认路径与文件名配置区 (可按需修改)
# ==========================================
DEFAULT_TXT_DIR = "Image\Archive\Msg2Resource_ej\etc\message"               # 合并后的 txt 文件夹路径
DEFAULT_MSG_ORIGIN_DIR = "Image\Archive\Msg2Resource_j\etc\message"       # 原始日文 msg 文件夹路径
DEFAULT_TBL_DEFAULT = "font00_j.tbl"       # 默认基础码表 (垫底使用)
DEFAULT_TBL_CUSTOM = "font00_custom.tbl"           # 自定义码表 (优先级更高，会覆盖默认码表) ### 此项字宽覆盖没有任何作用🙃
DEFAULT_OUT_DIR = "Image\Archive\Msg2Resource_ej\etc\message"     # 最终输出 msg 的文件夹路径
# ==========================================

def load_tbl(tbl_path, char_to_data):
    """
    读取单个 tbl 码表文件并更新到字典中。
    由于字典的特性，后读取的键值对会自动覆盖之前已存在的同名键值对。
    """
    if not os.path.exists(tbl_path):
        print(f"提示: 找不到码表文件 '{tbl_path}'，将跳过读取该文件。")
        return False
        
    loaded_count = 0
    with open(tbl_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                char_id = int(row['ID'])
                char_width = int(row['Width'])
                char_to_data[row['Char']] = (char_id, char_width)
                loaded_count += 1
            except (ValueError, KeyError):
                continue
                
    print(f"成功从 '{tbl_path}' 加载了 {loaded_count} 个字符数据。")
    return True

def process_single_msg(txt_input, msg_origin, msg_output, char_to_data):
    """处理单个 msg 文件的提取和重新打包"""
    # 1. 提取原始 msg 的文件头 (前 0x40 字节)
    try:
        with open(msg_origin, 'rb') as f:
            header_data = f.read(0x40)
    except FileNotFoundError:
        print(f"跳过: 找不到原始 msg 文件 {msg_origin}")
        return False

    # 2. 读取合并后的 txt
    try:
        with open(txt_input, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"跳过: 找不到 txt 文件 {txt_input}")
        return False

    blocks = re.findall(r'\[Line (\d+)\]\n(.*?)(?=\n\n\[Line|\Z)', content, re.DOTALL)
    
    # 3. 写入新的 msg 文件
    with open(msg_output, 'wb') as f:
        f.write(header_data) # 写入原始文件头
        
        # 匹配 {id,width} 标签 或 单个普通字符
        pattern = re.compile(r'\{(\d+),(\d+)\}|(.)', re.DOTALL)

        for _, text in blocks:
            text = text.strip()
            
            for match in pattern.finditer(text):
                if match.group(1): # 这是一个控制符标签
                    char_id = int(match.group(1))
                    char_width = int(match.group(2))
                else: # 这是一个普通字符
                    char = match.group(3)
                    if char == '\n':
                        char_id, char_width = 0, 1027  # 将文本换行符重新转回 {0,1027} 二进制
                    elif char in char_to_data:
                        char_id, char_width = char_to_data[char]
                    else:
                        print(f"警告: 字符 '{char}' 不在任何码表中或信息被忽略，已用 0 占位。")
                        char_id, char_width = 0, 0
                
                f.write(struct.pack('<HH', char_id, char_width))
            
            # 强制写入句末结束符 {0,1025}
            f.write(struct.pack('<HH', 0, 1025))
            
    return True

def main():
    # 为了保留灵活性，如果用户依然从命令行传参，则优先使用命令行参数；
    # 如果没有传参（例如直接双击运行），则使用脚本内部的默认配置。
    txt_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TXT_DIR
    msg_origin_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MSG_ORIGIN_DIR
    out_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT_DIR
    
    if not os.path.exists(txt_dir):
        print(f"错误: 找不到 txt 输入文件夹 '{txt_dir}'")
        return
        
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    char_to_data = {}
    
    # 1. 优先读取默认/基础码表 (垫底)
    load_tbl(DEFAULT_TBL_DEFAULT, char_to_data)
    
    # 2. 再读取自定义码表 (如果存在同名字段，新数据会自动覆盖字典里的旧数据)
    load_tbl(DEFAULT_TBL_CUSTOM, char_to_data)
    
    if not char_to_data:
        print("错误: 没有成功加载任何码表数据，请检查 tbl 文件是否存在或格式是否正确。")
        return

    # 3. 遍历 txt 文件夹进行批量转换
    processed_count = 0
    for filename in os.listdir(txt_dir):
        if not filename.endswith('.txt'):
            continue
            
        # 智能提取基础文件名，剥离各种可能的后缀
        base_name = filename
        if base_name.endswith('.txt'):
            base_name = base_name[:-4]
            
        if base_name.endswith('_ej'):
            base_name = base_name[:-3]
        elif base_name.endswith('_j'):
            base_name = base_name[:-2]
        elif base_name.endswith('_e'):
            base_name = base_name[:-2]
            
        # 构建对应的原始 j.msg 文件名和最终输出的 j.msg 文件名
        origin_msg_name = f"{base_name}_j.msg"
        out_msg_name = f"{base_name}_j.msg"
        
        txt_path = os.path.join(txt_dir, filename)
        origin_msg_path = os.path.join(msg_origin_dir, origin_msg_name)
        out_msg_path = os.path.join(out_dir, out_msg_name)
        
        if process_single_msg(txt_path, origin_msg_path, out_msg_path, char_to_data):
            print(f"已生成: {out_msg_name}")
            processed_count += 1

    print(f"\n批量导入完成，共处理了 {processed_count} 个 msg 文件，已保存至: {out_dir}")
    print("注意: 仅复制了前 0x40 字节文件头。由于文本长度改变，引擎寻址所需的文件头指针(Offsets)可能需要后续重新计算。")

if __name__ == '__main__':
    main()