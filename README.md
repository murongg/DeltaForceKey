# 三角洲交易行抢卡助手


## 介绍

### 交流 QQ 群： 885499673，内附使用教程

## 使用方法

> python 版本要求 3.10 以上

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行
```bash 
python main.py
```

### 构建
```bash
pyinstaller --name "牛角洲交易行抢货助手" --add-data ".\*.json;." --add-data ".\resources;resources" --icon ".\resources\images\icon.ico" --windowed --noconfirm --additional-hooks .\hooks --collect-all paddle --collect-all paddleocr --collect-all tqdm .\main.py```
```
## 软件截图
![image](./images/window.png)

## 免责声明
本软件仅供学习交流使用，禁止用于任何商业用途。使用本软件所产生的任何后果与作者无关。请在法律允许的范围内使用本软件，遵守相关法律法规。

## 捐助

如果你觉得本项目对你有帮助，可以考虑捐助我，支持我继续开发和维护这个项目。

<img src="./images/wechat.png" alt="微信" width="400" />