import json
import os
import sys

from constants import CONFIG_PATH


def get_config_path():
    """获取 config.json 的路径"""
    return CONFIG_PATH

def check_or_create_config():
    """检查 config.json 是否存在，如果不存在则创建一个空的 config.json"""
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        print("配置文件不存在，已创建空的 config.json")
    else:
        print("配置文件已存在")


def read_config_field(field, default=None):
    """读取 config.json 中指定字段的值"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get(field, default)
    except FileNotFoundError:
        return default

def read_all_config():
    """读取 config.json 中所有字段的值"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        return {}


def write_config_field(field, value):
    """写入 config.json 中指定字段的值"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    config[field] = value

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


