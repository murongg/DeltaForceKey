import os
import sys

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR,"config.json")
RESOURCE_PATH = os.path.join(BASE_DIR,"resources")
ICON_PATH = os.path.join(RESOURCE_PATH,"images\icon.ico")