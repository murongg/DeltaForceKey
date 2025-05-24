import time

import pyautogui
import pygetwindow as gw

from selection_window import SelectionWindow

def check_game_window(self, parent):
    """检查游戏窗口是否存在"""
    # 获取并激活窗口标题包含“三角洲”的窗口
    target_window = None
    for window in gw.getAllTitles():
        if "三角洲" in window:  # 模糊匹配窗口标题
            target_window = gw.getWindowsWithTitle(window)[0]
            break

    if target_window:
        target_window.activate()  # 激活“三角洲”窗口

        print(f"已激活窗口：{target_window.title}")

        # 最小化主窗口
        parent.showMinimized()

        # 打开全屏透明窗口
        self.selection_window = SelectionWindow(self)
        self.selection_window.show()

        # 再次激活全屏透明窗口
        time.sleep(0.2)  # 等待窗口激活
        self.selection_window.activateWindow()
        self.selection_window.setFocus()

        return True
    else:
        return False


def switch_game_window():
    """检查游戏窗口是否存在"""
    # 获取并激活窗口标题包含“三角洲”的窗口
    target_window = None
    for window in gw.getAllTitles():
        if "三角洲" in window:  # 模糊匹配窗口标题
            target_window = gw.getWindowsWithTitle(window)[0]
            break

    if target_window:
        target_window.activate()  # 激活“三角洲”窗口
        print(f"已激活窗口：{target_window.title}")
        return True
    else:
        return False


def get_list_map_index(list_map, key, val):
    """获取列表中元素的索引"""
    index = [i for i, item in enumerate(list_map) if item[key] == val]
    return index[0] if index else -1

def take_screenshot(region, threshold):
    """截取指定区域的截图并二值化"""
    try:
        screenshot = pyautogui.screenshot(region=region)
        gray_image = screenshot.convert("L")  # 转换为灰度图像
        # binary_image = gray_image.point(lambda p: 255 if p > threshold else 0)
        # binary_image = Image.eval(binary_image, lambda x: 255 - x)
        screenshot.close()
        return gray_image
    except Exception as e:
        print(f"[错误] 截图失败: {str(e)}")
        return None
