import time

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QBoxLayout, QMessageBox, QMainWindow

from config import read_config_field, write_config_field
from product_item_ui import Ui_ProductFrom
from selection_window import SelectionWindow
from utils import check_game_window


class ProductConfigItemData:
    """商品配置项数据"""

    def __init__(self, name, type, expect_price, floating_percentage_range, enable_buy, buy_count, already_buy_count, position):
        self.name = name
        self.type = type
        self.expect_price = expect_price
        self.floating_percentage_range = floating_percentage_range
        self.enable_buy = enable_buy
        self.buy_count = buy_count
        self.already_buy_count = already_buy_count
        self.position = position

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "expect_price": self.expect_price,
            "floating_percentage_range": self.floating_percentage_range,
            "enable_buy": self.enable_buy,
            "buy_count": self.buy_count,
            "already_buy_count": self.already_buy_count,
            "position": self.position
        }


class ProductItem(QWidget):
    save_signal = QtCore.pyqtSignal(ProductConfigItemData, int)
    remove_signal = QtCore.pyqtSignal(int)
    select_position_signal = QtCore.pyqtSignal(int)

    position = []

    def __init__(self, index: int):
        super().__init__()
        self.index = index
        self.form = Ui_ProductFrom()
        self.form.setupUi(self)
        self.__connect_signal_to_slot__()

    def set_data(self, data: ProductConfigItemData):
        """设置商品配置项数据"""
        self.form.product_name.setText(data.name)
        self.form.expect_price.setValue(data.expect_price)
        self.form.floating_percentage_range.setValue(data.floating_percentage_range)
        self.form.buy_count.setValue(data.buy_count)
        self.form.already_buy_count.setText(str(data.already_buy_count))
        self.form.position.setText(str(data.position))
        self.form.product_item_box.setTitle(data.name)
        self.form.product_item_box.setChecked(data.enable_buy)
        self.position = data.position

    def save(self):
        """保存商品配置项数据"""
        data = ProductConfigItemData(
            name=self.form.product_name.text(),
            type="",
            expect_price=self.form.expect_price.value(),
            floating_percentage_range=self.form.floating_percentage_range.value(),
            enable_buy=self.form.product_item_box.isChecked(),
            buy_count=int(self.form.buy_count.value()),
            already_buy_count=int(self.form.already_buy_count.text()),
            position=self.position
        )
        self.save_signal.emit(data, self.index)
        return data

    def remove(self):
        """删除商品配置项数据"""
        self.remove_signal.emit(self.index)

    def select_position(self):
        """选择商品位置"""
        self.select_position_signal.emit(self.index)

    def clear_buy_count(self):
        """清空已购买数量"""
        self.form.already_buy_count.setText("0")
        self.save()

    def set_name(self, name: str):
        """设置商品名称"""
        self.form.product_item_box.setTitle(name)

    def __connect_signal_to_slot__(self):
        """连接信号"""
        self.form.save_btn.clicked.connect(self.save)
        self.form.del_btn.clicked.connect(self.remove)
        self.form.select_position_btn.clicked.connect(self.select_position)
        self.form.product_item_box.toggled.connect( self.save)
        self.form.clear_buy_btn.clicked.connect(self.clear_buy_count)
        self.form.product_name.textChanged.connect(lambda: self.set_name(self.form.product_name.text()))

class Products:
    def __init__(self, layout: QBoxLayout, parent:Ui_ProductFrom = None, window:QMainWindow = None):
        """商品配置项管理类"""
        super().__init__()
        self.parent = parent
        self.window = window
        self.selection_window = SelectionWindow(self)
        self.selection_window_index = None
        self.layout = layout
        self.products = []
        self.product_widgets = []
        self.read_config()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        for index, item in enumerate(self.products):
            data = ProductConfigItemData(
                name=item.get("name"),
                type=item.get("type"),
                expect_price=item.get("expect_price"),
                floating_percentage_range=item.get("floating_percentage_range"),
                enable_buy=item.get("enable_buy"),
                buy_count=item.get("buy_count"),
                already_buy_count=item.get("already_buy_count"),
                position=item.get("position")
            )
            self.add_product_item(data, index)

    def add_product_item(self, data: ProductConfigItemData, index: int):
        product_item = ProductItem(index)
        product_item.set_data(data)
        product_item.save_signal.connect(self.write_config)
        product_item.remove_signal.connect(self.remove_product)
        product_item.select_position_signal.connect(self.select_position)
        self.product_widgets.append(product_item)
        self.layout.addWidget(product_item)

    def select_position(self, index:int):
        """选择商品位置"""
        self.selection_window_index = index
        if check_game_window(self, self.window) is False:
            QMessageBox.warning(self.window, "提示", "请先启动游戏")
            return

    def set_selection_area(self, x1, y1, x2, y2):
        """设置选择区域"""
        self.product_widgets[self.selection_window_index].position = [x1, y1, x2, y2]
        self.product_widgets[self.selection_window_index].form.position.setText(str([x1, y1, x2, y2]))
        self.product_widgets[self.selection_window_index].save()
        self.selection_window.hide()

    def read_config(self):
        """读取配置文件"""
        self.products = read_config_field("products")

    def write_config(self,data:ProductConfigItemData, index:int):
        """写入配置文件"""
        self.products[index] = data.to_dict()
        write_config_field("products", self.products)

    def remove_product(self, index:int):
        """删除商品配置项数据"""
        self.products.pop(index)
        write_config_field("products", self.products)
        # 更新布局
        self.product_widgets[index].deleteLater()

    def add_product(self):
        """添加商品配置项"""
        index = len(self.product_widgets)
        data = ProductConfigItemData(
            name="",
            type="",
            expect_price=0,
            floating_percentage_range=0,
            enable_buy=True,
            buy_count=0,
            already_buy_count=0,
            position=[0, 0]
        )
        self.add_product_item(data, index)
        self.products.append(data.to_dict())
        self.write_config(data, index)

