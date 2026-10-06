# re5-research
生化危机5游戏文本编辑工具。

## 使用方法

### 文本导入导出

```python
python re5_msg2txt.py <文件名或文件夹路径> # 导出时同步更新码表font00_j.tbl中的字宽
python re5_txt2msg.py <文件名或文件夹路径>
```

导出txt格式示例：

```
[Line 0]
Yes

[Line 1]
No

[Line 2]
OK
```

### 日英文本合并

可在脚本内配置合并文件路径，或通过参数传入。

```python
python merge_txt.py 
```

### 行数检查

检查txt中是否有文本块超出配置中指定的行数。

```python
python line_check.py <文件夹路径>
```

### 自定义字库贴图

根据指定字体和码表生成与`font00_j.tex`相同格式的字库贴图。

```python
python generate_custom_dds.py
```

### 自定义码表

根据指定字体和字符生成包含字宽的码表。

```python
generate_custom_tbl.py
```

## 游戏

### 字库

中文以外的字库路径：`nativePC_MT\Image\Archive\CoreResource\etc\message\font00_j.tex`

字库贴图的压缩方式是**无**。字符排列为左对齐。

英文字体1651 Alchemy Normal，日文字体華康郭泰碑（包括全角英数）。原生未考虑日英混排。

### 文本

文本路径：`nativePC_MT\Image\Archive\Msg2Resource_x`，x是语言。

#### 文本编码格式

小端序4字节编码，前两个字节为字库顺序自定义编码，后两个字节为字符宽度。这个字符宽度没有任何作用。

#### 控制符

4字节编码前两个字节为0+后两个字节=控制符。

`00 00 01 04`：1025，文本块结束
`00 00 03 04`：1027，换行符
`00 00 10 04`：1040，文件使用，居中
`00 00 11 04`：1041，文件使用，取消居中
`00 00 12 04 xx xx 12 04 xx xx 12 04`：{0,1042}{x,1042}{y,1042}，字号，x是宽，y是高，按照x=y设置。
`00 00 13 04`：1043，字号-
`00 00 14 04`：1044，结束字号-
`00 00 15 04`：1045，字号+
`00 00 16 04`：1046，结束字号+
`00 00 19 04 xx xx 19 04`：{0,1049}{x,1049}，按键图标，x为UI编号
`00 00 1A 04 xx xx 1A 04`：{0,1050}{x,1050}，按键图标
`00 00 1C 04 xx xx 1C 04`：{0,1052}{x,1052}，调用当前文件第x块文本
`00 00 22 04`：1058，斜体
`00 00 23 04`：1059，结束斜体
`00 00 1F 04 xx xx 1F 04`：{0,1055}{x,1055}，文字颜色，x为颜色编号，1=黑，2=红，3=绿，4=蓝，5=黄，6=白，其他为灰色
`00 00 26 04`：1062，段落居右（效果比较奇怪）
`00 00 26 04`：1063，段落居左
`00 00 28 04 xx xx 28 04`：{0,1064}{x,1064}，角色，x为角色编号
`00 00 2B 04`：1067，物品名，调用字符串
`00 00 2D 04`：1069，数字（物品数量），调用字符串
`00 00 2E 04 xx xx 2E 04`：{0,1070}{x,1070}，按键图标
`00 00 2F 04 xx xx 2F 04`：{0,1071}{x,1071}，按键图标
`00 00 30 04 06 00 30 04 02 00 30 04`：{0,1072}{6,1072}{2,1072}，疑似上下左右偏移
`00 00 31 04`：{0,1073}，不明，疑似结束标签
`00 00 32 04`：{0,1074}，不明，疑似结束标签

### 字符宽度控制函数

`re5dx9.exe`

```assembly
007DBE0B | 0FB732               | movzx esi,word ptr ds:[edx]      ; 读取当前字符的 ID
007DBE0E | 66:81FE 6E02         | cmp si,26E                       ; 【关键判断】判断 ID 是否大于 0x26E (十进制 622)
007DBE1A | 0FB7CE               | movzx ecx,si
007DBE1D | 77 0E                | ja re5dx9.7DBE2D                 ; 如果大于 622 (中日文)，跳走去读 8 字节结构体表！
007DBE1F | D1E9                 | shr ecx,1                        ; 【高速通道】如果小于 622 (英文/数字)，将 ID 除以 2
007DBE21 | 8A81 E84EF600        | mov al,byte ptr ds:[ecx+F64EE8]  ; 从静态地址 00F64EE8 处，只读取 1 个 byte 作为宽度
```

## 其他

### 文本容量上限

大部分msg文本的内存分配上限是200KB左右（stage压到204KB时仍然存在读不出来的情况），超过长度的会被丢弃，导致局内对话语音消失。

文件文本超长会内存溢出，导致游戏卡死崩溃。

### 字宽相关dll

基于[RE5Fix](https://github.com/Lyall/RE5Fix)修改和编译。


```csharp
// ========================================================
// 静态映射表绝对地址
// ========================================================
const DWORD ASCII_TABLE_BASE = 0x00F64EE8; // 英文/数字 专用单字节高速表
const DWORD ASIAN_TABLE_BASE_1 = 0x010CCB10; // 中/日文 专用 8 字节结构体表主备份
const DWORD ASIAN_TABLE_BASE_2 = 0x010D76F0; // 中/日文 专用 8 字节结构体表副备份
const std::string TBL_FILENAME = "font00_custom.tbl";

// 覆写 4 字节数据 (用于中日文表)
void PatchMemoryInt(DWORD address, int value)
{
	DWORD oldProtect;
	VirtualProtect((void*)address, 4, PAGE_EXECUTE_READWRITE, &oldProtect);
	*(int*)address = value;
	VirtualProtect((void*)address, 4, oldProtect, &oldProtect);
}

// 覆写 1 字节数据 (用于英文数字表)
void PatchMemoryByte(DWORD address, uint8_t value)
{
	DWORD oldProtect;
	VirtualProtect((void*)address, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
	*(uint8_t*)address = value;
	VirtualProtect((void*)address, 1, oldProtect, &oldProtect);
}

bool LoadAndApplyCustomTbl()
{
	std::ifstream file(TBL_FILENAME);
	if (!file.is_open())
	{
		std::cout << "[错误] 找不到码表文件: " << TBL_FILENAME << std::endl;
		return false;
	}

	std::string line;
	bool firstLine = true;
	int successCount = 0;

	while (std::getline(file, line))
	{
		if (firstLine) { firstLine = false; continue; }
		if (line.empty()) continue;

		size_t lastComma = line.rfind(',');
		if (lastComma == std::string::npos) continue;
		size_t secondLastComma = line.rfind(',', lastComma - 1);
		if (secondLastComma == std::string::npos) continue;

		std::string idStr = line.substr(secondLastComma + 1, lastComma - secondLastComma - 1);
		std::string widthStr = line.substr(lastComma + 1);

		try
		{
			int id = std::stoi(idStr);
			int width = std::stoi(widthStr);

			// ==========================================
			// 核心分流逻辑：根据引擎底层汇编规律分配内存
			// ==========================================
			if (id <= 622) // 即汇编中的 0x26E
			{
				// 英文字符通道：
				// 寻址公式：基址 + (ID / 2)
				DWORD targetAddr = ASCII_TABLE_BASE + (id / 2);

				// 因为引擎用的是 mov al (8位寄存器)，最大只能读 255，超过会导致溢出乱码
				if (width > 255) width = 255;

				PatchMemoryByte(targetAddr, (uint8_t)width);
			}
			else
			{
				// 亚洲字符通道：
				// 寻址公式：基址 + (ID * 8)
				DWORD targetAddr1 = ASIAN_TABLE_BASE_1 + (id * 8);
				DWORD targetAddr2 = ASIAN_TABLE_BASE_2 + (id * 8);

				PatchMemoryInt(targetAddr1, width);
				PatchMemoryInt(targetAddr2, width);
			}

			successCount++;
		}
		catch (...) {}
	}

	std::cout << "[成功] 字宽物理内存覆写完毕！生效字符数: " << successCount << std::endl;
	return true;
}

// =========== 重点修改 Main 线程 ===========
DWORD __stdcall Main(void*)
{
	Sleep(1000); // 初始等待

#if _DEBUG
	AllocConsole();
	freopen_s((FILE**)stdout, "CONOUT$", "w", stdout);
	std::cout << "Console initiated" << std::endl;
#endif	

	// 核心：尝试覆写字宽，如果失败或游戏尚未映射完全，可以反复重试
	std::cout << "开始尝试覆写字宽..." << std::endl;
	bool applied = false;
	// 尝试循环最多 10 次，每次间隔 1 秒，确保引擎初始化完毕且不被覆盖
	for (int i = 0; i < 10; ++i)
	{
		applied = LoadAndApplyCustomTbl();
		if (applied)
		{
			break;
		}
		Sleep(1000);
	}

	if (!applied)
	{
		std::cout << "[警告] 超过 10 秒仍未成功读取并覆写 font00_custom.tbl" << std::endl;
	}

	return true;
}
```

## 致谢

99.9% 的代码由 Gemini Pro 编写 :)

