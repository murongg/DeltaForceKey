import logging
import sys

import keyboard
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from basic_config import BasicConfig
from config import read_all_config
from constants import ICON_PATH
from logger import configure_log_system, LogDisplayController
from product_item import Products
from rush import Rush
from ui import Ui_MainWindow

class Main(Ui_MainWindow):
    def __init__(self, window=QMainWindow):
        super().__init__()
        self.window = window
        self.basic_config = None
        self.product_widget = None
        self.config = None
        self.read_config()

    def setup(self):
        self.set_product_list()
        self.set_basic_config()
        self.set_logger()
        self.logger = logging.getLogger("app")
        self.rush = Rush(self)
        keyboard.add_hotkey("ctrl+1", lambda: self.rush.start())
        keyboard.add_hotkey("ctrl+2", lambda: self.rush.stop())
        self.__connect_signal_to_slot__()

    def set_product_list(self):
        self.product_widget = Products(self.product_config_scroll_area_layout, self, self.window)
        self.product_config_scroll_area_widget.adjustSize()
        self.product_config_scroll_area.updateGeometry()

    def set_logger(self):
        # 设置日志窗口
        try:
            self.log_controller = LogDisplayController(self.log_text)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"日志初始化失败: {str(e)}")
            self.close()

    def product_config_scroll_area_scroll_to_bottom(self):
        # 确保使用正确的滚动区域控件
        scroll_area = self.product_config_scroll_area
        scroll_bar = scroll_area.verticalScrollBar()
        QTimer.singleShot(300, lambda: scroll_bar.setValue(scroll_bar.maximum()))
        
    def set_basic_config(self):
        # 设置基本配置
        self.basic_config = BasicConfig(self, self.config)

    def read_config(self):
        # 读取配置文件
        self.config = read_all_config()

    def add_product(self):
        current_tab_index = self.main_tab_widget.currentIndex()
        if current_tab_index != 1:
            self.main_tab_widget.setCurrentIndex(1)
        self.product_widget.add_product()
        self.product_config_scroll_area_scroll_to_bottom()

    def __connect_signal_to_slot__(self):
        # 连接信号和槽
        self.add_product_menu.aboutToShow.connect(lambda: self.add_product())
        self.start_btn.clicked.connect(lambda: self.rush.start())
        self.stop_btn.clicked.connect(lambda: self.rush.stop())

# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    app = QApplication(sys.argv)
    configure_log_system()
    MainWindow = QtWidgets.QMainWindow()
    MainWindow.setWindowTitle('牛角洲交易行抢货助手v1.0 交流QQ群：885499673')
    MainWindow.setWindowIcon(QIcon(ICON_PATH))
    ui = Main(MainWindow)
    ui.setupUi(MainWindow)
    ui.setup()
    MainWindow.show()
    sys.exit(app.exec_())

