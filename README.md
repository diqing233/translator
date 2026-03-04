# 快速翻译 / Quick Translator

一个简洁的 Windows 桌面翻译软件，基于 Python + tkinter，使用 Google 翻译（无需 API Key）。

![界面预览](preview.png)

## 功能特性

- 支持 19 种语言互译
- 自动翻译（输入停顿后自动触发）
- `Ctrl+Enter` 手动翻译
- `Ctrl+T` 窗口置顶
- 一键复制翻译结果
- 语言互换按钮
- 深色主题界面
- **无需 API Key，完全免费**

## 使用方法

### 方式一：直接运行（需要 Python）

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/translator.git
cd translator

# 2. 直接运行（无需安装依赖）
python translator.py
```

### 方式二：打包为 .exe

```bash
# 双击运行 build.bat，或在终端执行：
pip install pyinstaller
pyinstaller --onefile --windowed --name "快速翻译" translator.py
# exe 文件生成在 dist/ 目录
```

## 系统要求

- Windows 10 / 11
- Python 3.8+（直接运行时需要）
- 网络连接（需能访问 Google 服务，建议开启代理）

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 立即翻译 |
| `Ctrl+T` | 窗口置顶/取消置顶 |

## 注意事项

- 本项目使用非官方 Google 翻译接口，在中国大陆需要挂代理使用
- 纯标准库实现，无第三方依赖

## License

MIT
