import datetime
import logging
import os
import threading
import time
import traceback
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pyautogui
from PyQt5.QtCore import QObject, pyqtSignal

os.environ["TQDM_DISABLE"] = "1"

from paddleocr import PaddleOCR

from config import read_all_config, write_config_field
from utils import switch_game_window, get_list_map_index, take_screenshot

# 常量定义
OCR_CONFIG = {
    'ch': {
        'lang': 'ch',
        'use_angle_cls': True,  # 修正参数名
        'cls_model_dir': None,   # 自动下载模型
        'show_log': False
    },
    'en': {
        'lang': 'en',
        'use_angle_cls': False,  # 英文不需要角度检测
        'show_log': False
    }
}
CONFIG_REQUIREMENTS = {
    'regions': ['buy_message_location', 'trade_btn_location', 'product_name_location', 'product_price_location'],
}
UI_DELAY = 0.1
MAX_THREAD_JOIN_TIMEOUT = 5
SCREENSHOT_THRESHOLD = 100
PRICE_THRESHOLD = 55

class Rush(QObject):
    """自动抢购核心逻辑控制器"""

    stopped = pyqtSignal()
    bought = pyqtSignal(int, object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__()
        self.parent = parent
        self._init_ocr_models()
        self._runtime_config: Dict[str, Any] = {}
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._active_card_list: List[Dict] = []
        self._setup_display_params()

    def _init_ocr_models(self):
        """初始化OCR模型实例"""
        self.ocr_ch: Optional[PaddleOCR] = None
        self.ocr_en: Optional[PaddleOCR] = None

    def _setup_display_params(self):
        """初始化显示相关参数"""
        self.screen_width, self.screen_height = pyautogui.size()
        self.parent.logger.debug(f"屏幕分辨率: {self.screen_width}x{self.screen_height}")

    def refresh_config(self):
        """刷新运行时配置"""
        try:
            config = read_all_config()
            self._validate_config(config)

            self._runtime_config = {
                'operation_mode': {
                    'is_loop': config.get("is_loop", False),
                    'is_debug': config.get("is_debug", False)
                },
                'ui_elements': {
                    'trade_btn': config.get("trade_btn_location", []),
                    'buy_btn': config.get("buy_btn_location", [0.825, 0.86]),
                    'message_region': config.get("buy_message_location", []),
                    'product_name_location': config.get("product_name_location", []),
                    'product_price_location': config.get("product_price_location", [])
                },
                'products': config.get("products", []),
                'screen': (self.screen_width, self.screen_height),
                'exec_interval': config.get("exec_interval", 0.1),
                'buy_confirm_interval': config.get("buy_confirm_interval", 0.5)
            }

            self.parent.logger.info("配置刷新成功")
        except Exception as e:
            self.parent.logger.error("配置刷新失败: %s", str(e))
            raise

    def _validate_config(self, config: Dict):
        """验证必要配置项完整性"""
        missing = [key for key in CONFIG_REQUIREMENTS['regions']
                   if not self._is_valid_region(config.get(key))]
        if missing:
            raise ValueError(f"缺少必要区域配置: {missing}")

        valid_products = len(config.get("products", [])) != 0
        if not valid_products:
            raise ValueError("未找到有效商品配置")

    @staticmethod
    def _is_valid_region(region: List) -> bool:
        """验证区域配置有效性"""
        return len(region) == 4 if region else False

    def start(self):
        """启动抢购流程"""
        if self._worker_thread and self._worker_thread.is_alive():
            self.parent.logger.warning("操作线程已在运行中")
            return

        try:
            self._prepare_operation()
            self._worker_thread = threading.Thread(
                target=self._purchase_workflow,
                daemon=True
            )
            self._worker_thread.start()
            self.parent.logger.info("抢购流程已启动")
        except Exception as e:
            s = traceback.format_exc()
            self.parent.logger.error("启动失败: %s", str(e))
            self.parent.logger.error("详细错误信息: %s", s)
            self.stop()

    def _prepare_operation(self):
        """执行操作前准备"""
        self._stop_event.clear()
        self.refresh_config()
        self._init_ocr_engines()

        if not switch_game_window():
            raise RuntimeError("游戏窗口切换失败")

        self._switch_to_trading()
        self._prepare_shopping_list()
        self.parent.logger.info("操作准备就绪")

    def _init_ocr_engines(self):
        """初始化OCR识别引擎"""
        try:
            ch = OCR_CONFIG['ch']
            en = OCR_CONFIG['en']
            self.ocr_ch = PaddleOCR(use_angle_cls=ch['use_angle_cls'],
                                    lang=ch['lang'],
                                    show_log=ch['show_log'])
            self.ocr_en = PaddleOCR(use_angle_cls=en['use_angle_cls'],
                                    lang=en['lang'],
                                    show_log=en['show_log'])

            self.parent.logger.debug("OCR引擎初始化成功")
        except Exception as e:
            self.parent.logger.error("OCR引擎初始化失败: %s", str(e))
            raise e

    def _switch_to_trading(self):
        """切换到交易行界面"""
        trade_btn = self._runtime_config['ui_elements']['trade_btn']
        x, y = self._get_center_position(trade_btn)
        self._perform_click(x, y)
        self.parent.logger.info("已进入交易行")

    def _prepare_shopping_list(self):
        """准备待购商品列表"""
        self._active_card_list = [
            card for card in self._runtime_config['products']
            if card.get('enable_buy', False)
               and card.get('buy_count', 0) > card.get('already_buy_count', 0)
        ]

        if not self._active_card_list:
            raise ValueError("没有有效的购买目标")

        self.parent.logger.info("待购清单: %s",
                    [card['name'] for card in self._active_card_list])

    def _purchase_workflow(self):
        """商品抢购主流程"""
        try:
            while not self._stop_event.is_set() and self._active_card_list:
                for card in list(self._active_card_list):
                    if self._stop_event.is_set():
                        return

                    self._process_single_card(card)
                    self._cleanup_inactive_cards()

                if not self._runtime_config['operation_mode']['is_loop']:
                    break

        except Exception as e:
            self.parent.logger.error("抢购流程异常: %s", str(e))
        finally:
            self._shutdown()

    def _process_single_card(self, card: Dict):
        """处理单个商品购买流程"""
        self.parent.logger.info("正在处理商品: %s", card['name'])

        try:
            if self._attempt_purchase(card):
                self._handle_success_purchase(card)
                if not self._runtime_config['operation_mode']['is_loop']:
                    self._active_card_list.remove(card)
        except Exception as e:
            self.parent.logger.error("商品处理失败: %s - %s", card['name'], str(e))

    def _attempt_purchase(self, card: Dict) -> bool:
        """执行完整购买尝试"""

        self._navigate_to_product(card)

        if not self._validate_product_identity(card):
            return False

        price_info = self._get_price_information()
        if not price_info['valid']:
            return False

        if self._is_acceptable_price(price_info, card):
            return self._execute_purchase(card, price_info)

        self.parent.logger.info("价格超出接受范围")
        self._cancel_operation()
        return False

    def _navigate_to_product(self, card: Dict):
        """导航到指定商品"""
        position = card.get('position', [])
        if len(position) != 4:
            raise ValueError("无效的商品位置配置")

        x, y = self._get_center_position(position)
        self._perform_click(x, y)
        time.sleep(self._runtime_config['exec_interval'])

    def _validate_product_identity(self, card: Dict) -> bool:
        """验证商品身份"""
        detected_name = self._get_product_name()
        expected_name = card['name'].replace(" ", "")

        if not detected_name:
            self.parent.logger.warning("未能识别商品名称")
            self._cancel_operation()
            return False

        if detected_name not in expected_name:
            self.parent.logger.warning("商品不匹配 (识别: %s / 预期: %s)",
                           detected_name, expected_name)
            self._cancel_operation()
            return False

        return True

    def _get_price_information(self) -> Dict:
        """获取价格信息"""
        price_region = self._runtime_config['ui_elements'].get(
            'product_price_location', [])

        screenshot = take_screenshot(
            region=price_region,
            threshold=PRICE_THRESHOLD
        )

        raw_text = self._ocr_process_price(screenshot)

        return raw_text

    def _ocr_process_price(self, image) -> Dict:
        """OCR处理价格信息"""
        try:
            result = self.ocr_en.ocr(np.array(image), cls=False)
            if not result or not result[0]:
                return {'valid': False}


            raw_text = result[0][0][1][0]
            clean_text = ''.join(filter(str.isdigit, raw_text))

            return {
                'valid': bool(clean_text),
                'numeric_value': int(clean_text),
                'raw_text': raw_text
            }
        except Exception as e:
            self.parent.logger.error("价格识别失败: %s", str(e))
            return {'valid': False}

    def _get_product_name(self) -> Optional[str]:
        """获取商品名称（优化后的实现）"""
        region = self._runtime_config['ui_elements'].get('product_name_location')

        if not self._is_valid_region(region):
            self.parent.logger.error("商品名称区域配置无效")
            return None

        try:
            # 获取增强型截图
            screenshot = take_screenshot(
                region=region,
                threshold=SCREENSHOT_THRESHOLD,
            )

            if not screenshot:
                return None

            # 使用中文OCR识别
            result = self.ocr_ch.ocr(np.array(screenshot), cls=True)
            if not result or not result[0]:
                self.parent.logger.error("无法识别物品名称")
                return None

            # 多结果校验逻辑
            text = result[0][0][1][0]  # 获取第一个识别结果的文字部分

            return text.replace(" ", "").strip()
        except Exception as e:
            self.parent.logger.error("商品名称识别失败: %s", str(e))
            return None

    def _handle_success_purchase(self, card: Dict):
        """处理成功购买（优化后的实现）"""
        try:
            # 原子化更新操作
            # with threading.Lock():
            #     current_count = card.get('already_buy_count', 0)
            #     card['already_buy_count'] = current_count + 1

            self.parent.logger.info("成功处理购买: %s (累计%d次)",
                        card['name'], card['already_buy_count'])

        except Exception as e:
            self.parent.logger.error("购买处理异常: %s", str(e))

    def _is_acceptable_price(self, price_info: Dict, card: Dict) -> bool:
        """判断价格是否可接受"""
        expected = card.get('expect_price', 0)
        current = price_info.get('numeric_value', 0)
        tolerance = card.get('floating_percentage_range', 0)

        return current <= expected * (1 + tolerance)

    def _execute_purchase(self, card: Dict, price_info: Dict) -> bool:
        """执行购买操作"""
        buy_btn = self._runtime_config['ui_elements']['buy_btn']
        x, y = self._get_center_position(buy_btn)

        self._perform_click(x, y)
        time.sleep(self._runtime_config['buy_confirm_interval'])  # 等待交易完成

        if self._confirm_purchase_success():
            self._record_transaction(card, price_info)
            self._cancel_operation()
            return True

        return False

    def _confirm_purchase_success(self) -> bool:
        """确认购买是否成功"""
        message_region = self._runtime_config['ui_elements']['message_region']
        screenshot = take_screenshot(message_region, SCREENSHOT_THRESHOLD)

        if not screenshot:
            return False

        try:
            result = self.ocr_ch.ocr(np.array(screenshot), cls=True)
            return any("购买成功" in res[1][0] for res in result[0])
        except Exception as e:
            self.parent.logger.error("购买确认失败: %s", str(e))
            return False

    def _record_transaction(self, card: Dict, price_info: Dict):
        """记录交易信息"""
        log_entry = (
            f"购买时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S} | "
            f"物品名称: {card['name']} | "
            f"理想价格: {card['expect_price']} | "
            f"最高执行价格: {card['expect_price'] * (1 + card['floating_percentage_range'])} | "
            f"购买价格: {price_info['numeric_value']} | "
            f"溢价: {((price_info['numeric_value'] / card['expect_price']) - 1) * 100:.2f}%\n"
        )

        self.parent.logger.info(log_entry.strip())
        # self._write_log_file(log_entry)
        self._update_card_counter(card)

    # @staticmethod
    # def _write_log_file(content: str):
    #     """写入日志文件"""
    #     try:
    #         with open("logs.txt", "a", encoding="utf-8") as f:
    #             f.write(content)
    #     except Exception as e:
    #         self.parent.logger.error("日志写入失败: %s", str(e))

    def _update_card_counter(self, card: Dict):
        """更新购买计数器"""
        card['already_buy_count'] = card.get('already_buy_count', 0) + 1
        index = get_list_map_index(
            self._runtime_config['products'],
            'name',
            card['name']
        )

        if index != -1:
            write_config_field("products", self._runtime_config['products'])
            self.bought.emit(index, card)
            self.parent.logger.info("配置更新成功: %s", card['name'])
        else:
            self.parent.logger.warning("未找到商品配置项: %s", card['name'])

    def _cleanup_inactive_cards(self):
        """清理已完成购买的商品"""
        for card in list(self._active_card_list):
            if card.get('already_buy_count', 0) >= card.get('buy_count', 0):
                self._active_card_list.remove(card)
                self.parent.logger.info("商品已完成购买: %s", card['name'])

    def stop(self):
        """停止抢购流程"""
        self._stop_event.set()

        if self._worker_thread:
            self._worker_thread.join(MAX_THREAD_JOIN_TIMEOUT)
            if self._worker_thread.is_alive():
                self.parent.logger.warning("操作线程未能正常终止")
            self._worker_thread = None

        self._release_resources()
        self.stopped.emit()
        self.parent.logger.info("抢购流程已停止")

    def _release_resources(self):
        """释放系统资源"""
        self.ocr_ch = None
        self.ocr_en = None
        self.parent.logger.debug("OCR资源已释放")

    def _get_center_position(self, region: List) -> Tuple[float, float]:
        """计算区域中心坐标"""
        if len(region) != 4:
            raise ValueError("无效的区域配置")
        return (region[0] + region[2] / 2, region[1] + region[3] / 2)

    def _perform_click(self, x: float, y: float):
        """执行点击操作"""
        pyautogui.moveTo(x, y)
        if not self._runtime_config['operation_mode']['is_debug']:
            pyautogui.click()
            time.sleep(self._runtime_config['exec_interval'])

    def _cancel_operation(self):
        """取消当前操作"""
        pyautogui.press('esc')
        time.sleep(self._runtime_config['exec_interval'])

    def _shutdown(self):
        """执行关闭清理流程"""
        self._release_resources()
        self.stopped.emit()
        self.parent.logger.info("系统资源已释放")


if __name__ == '__main__':
    rush = Rush()
    rush.start()