from PyQt5.QtWidgets import (
    QApplication, QWidget
)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen

class SelectionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        # 设置窗口标志，确保全屏透明窗口覆盖其他应用程序
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setWindowModality(Qt.ApplicationModal)  # 设置为模态窗口
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.show_red_border = True  # 控制是否显示红色边框

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.globalPos()
            self.end_point = self.start_point
            self.is_selecting = True
            self.show_red_border = True  # 开始框选时显示红色边框
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            self.end_point = event.globalPos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if self.is_selecting:
            self.end_point = event.globalPos()
            self.is_selecting = False
            self.update()

            # 计算框选区域
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())
            width = x2 - x1
            height = y2 - y1

            # 打印框选区域
            print(f"框选区域：[x={x1}, y={y1}, 宽={width}, 高={height}]")

            # 将框选区域传递给主窗口
            self.parent.set_selection_area(x1, y1, width, height)

            # 截图框选区域
            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(0, x1, y1, width, height)

            # 显示截图到主窗口
            # self.parent.display_screenshot(screenshot)

            # 关闭红色边框的显示
            self.show_red_border = False
            self.update()

            # 关闭透明窗口
            self.close()

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:  # 检测是否按下 ESC 键
            print("ESC 键按下，退出框选窗口")
            self.close()  # 关闭透明窗口
            event.accept()  # 标记事件为已处理，防止传播到其他程序
        else:
            event.ignore()  # 对于其他按键，继续传播事件

    def paintEvent(self, event):
        """绘制框选区域和背景"""
        painter = QPainter(self)

        # 绘制半透明黑色背景
        painter.setOpacity(0.5)
        painter.fillRect(self.rect(), Qt.black)

        # 绘制框选区域
        if self.is_selecting:
            painter.setOpacity(0.3)
            painter.fillRect(QRect(self.start_point, self.end_point), Qt.white)
            if self.show_red_border:  # 仅在框选时显示红色边框
                painter.setOpacity(1.0)
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                rect = QRect(self.start_point, self.end_point)
                painter.drawRect(rect)
