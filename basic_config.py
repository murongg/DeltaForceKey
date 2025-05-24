import time
from enum import Enum

from PyQt5.QtWidgets import QMessageBox

from config import write_config_field
from selection_window import SelectionWindow
from ui import Ui_MainWindow
from utils import check_game_window


class PositionSettingName(Enum):
    """ 位置设置名称 """
    PRODUCT_NAME = "product_name_location"
    PRODUCT_PRICE = "product_price_location"
    BUY_BTN = "buy_btn_location"
    TRADE_BTN = "trade_btn_location"
    BUY_MESSAGE = "buy_message_location"

class BasicConfig:
    """
    Basic configuration class for a web application.
    """
    is_debug: bool = False
    is_loop: bool = False
    buy_btn_location = []
    product_name_location = []
    product_price_location = []
    trade_btn_location = []
    buy_message_location = []
    exec_interval = 0.1
    buy_confirm_interval = 0.5
    current_position_setting:PositionSettingName

    def __init__(self, parent: Ui_MainWindow, config: dict = None):
        self.parent = parent
        self.selection_window = SelectionWindow(self)
        self.is_debug = config.get("is_debug", False)
        self.is_loop = config.get("is_loop", False)
        self.buy_btn_location = config.get("buy_btn_location", [])
        self.product_name_location = config.get("product_name_location", [])
        self.product_price_location = config.get("product_price_location", [])
        self.trade_btn_location = config.get("trade_btn_location", [])
        self.buy_message_location = config.get("buy_message_location", [])
        self.exec_interval = config.get("exec_interval", 0.1)
        self.buy_confirm_interval = config.get("buy_confirm_interval", 0.5)

        self.init_ui()
        self.__connect_signal_to_slot__()

    def init_ui(self):
        self.parent.debug_mode.setChecked(self.is_debug)
        self.parent.loop_mode.setChecked(self.is_loop)
        self.parent.exec_interval_spin_box.setValue(self.exec_interval)
        self.parent.buy_confirm_interval_spin_box.setValue(self.buy_confirm_interval)
        self.parent.buy_btn_location_label.setText(f"交易行购买按钮位置：{self.buy_btn_location}")
        self.parent.product_name_location_label.setText(f"交易行商品名称位置：{self.product_name_location}")
        self.parent.product_price_location_label.setText(f"交易行商品价格位置：{self.product_price_location}")
        self.parent.trade_btn_location_label.setText(f"交易行交易按钮位置：{self.trade_btn_location}")
        self.parent.buy_message_location_label.setText(f"交易行购买提示位置：{self.buy_message_location}")


    def select_position(self, current_position_setting:PositionSettingName):
        self.current_position_setting = current_position_setting
        if check_game_window(self, self.parent.window) is False:
            QMessageBox.warning(self.parent.window, "提示", "请先启动游戏")
            return

    def set_selection_area(self, x1, y1, x2, y2):
        """设置选择区域"""
        self.selection_window.hide()
        location = [x1, y1, x2, y2]
        if self.current_position_setting == PositionSettingName.BUY_BTN:
            self.buy_btn_location = location
            self.parent.buy_btn_location_label.setText(f"交易行购买按钮位置：{self.buy_btn_location}")
        elif self.current_position_setting == PositionSettingName.PRODUCT_NAME:
            self.product_name_location = location
            self.parent.product_name_location_label.setText(f"交易行商品名称位置：{self.product_name_location}")
        elif self.current_position_setting == PositionSettingName.PRODUCT_PRICE:
            self.product_price_location = location
            self.parent.product_price_location_label.setText(f"交易行商品价格位置：{self.product_price_location}")
        elif self.current_position_setting == PositionSettingName.TRADE_BTN:
            self.trade_btn_location = location
            self.parent.trade_btn_location_label.setText(f"交易行交易按钮位置：{self.trade_btn_location}")
        elif self.current_position_setting == PositionSettingName.BUY_MESSAGE:
            self.buy_message_location = location
            self.parent.buy_message_location_label.setText(f"交易行购买提示位置：{self.buy_message_location}")

        # 更新配置文件
        self.write_config(self.current_position_setting.value, location)

    def write_config(self,key:str, value:object):
        """写入配置文件"""
        write_config_field(key, value)

    def set_debug_mode(self, is_debug:bool):
        """设置调试模式"""
        self.is_debug = is_debug
        self.write_config("is_debug", is_debug)

    def set_loop_mode(self, is_loop:bool):
        """设置循环模式"""
        self.is_loop = is_loop
        self.write_config("is_loop", is_loop)

    def set_exec_interval(self, interval:float):
        """设置执行间隔"""
        self.exec_interval = interval
        self.write_config("exec_interval", interval)

    def set_buy_confirm_interval(self, interval:float):
        """设置购买确认间隔"""
        self.buy_confirm_interval = interval
        self.write_config("buy_confirm_interval", interval)

    def __connect_signal_to_slot__(self):
        # 连接信号
        self.parent.buy_btn_location_btn.clicked.connect(lambda: self.select_position(PositionSettingName.BUY_BTN))
        self.parent.product_name_location_btn.clicked.connect(lambda: self.select_position(PositionSettingName.PRODUCT_NAME))
        self.parent.product_price_location_btn.clicked.connect(lambda: self.select_position(PositionSettingName.PRODUCT_PRICE))
        self.parent.trade_btn_location_btn.clicked.connect(lambda: self.select_position(PositionSettingName.TRADE_BTN))
        self.parent.buy_message_location_btn.clicked.connect(lambda: self.select_position(PositionSettingName.BUY_MESSAGE))
        self.parent.debug_mode.toggled.connect(self.set_debug_mode)
        self.parent.loop_mode.toggled.connect(self.set_loop_mode)
        self.parent.exec_interval_spin_box.valueChanged.connect(self.set_exec_interval)
        self.parent.buy_confirm_interval_spin_box.valueChanged.connect(self.set_buy_confirm_interval)
