"""Define simulation settings, body types, and localized interface text."""

from __future__ import annotations

from pathlib import Path


CONFIG = {
    "width": 1240,
    "height": 780,
    "panel_width": 300,
    "background": (7, 11, 20),
    "panel": (15, 22, 35),
    "panel_border": (37, 52, 72),
    "text": (228, 235, 246),
    "muted": (137, 153, 177),
    "accent": (94, 210, 190),
    "accent_2": (245, 174, 86),
    "danger": (238, 113, 113),
    "G": 1.0,
    "dt": 0.004,
    "softening": 0.65,
    "max_trail": 220,
    "permanent_max_trail": 6000,
    "max_bodies": 220,
    "prediction_steps": 2000,
    "prediction_max_steps": 6000,
    "prediction_body_diameters": 12,
}


BASE_DIR = Path(__file__).resolve().parent
PREFS_PATH = BASE_DIR / "prefs.json"
SCENE_PATH = BASE_DIR / "scene.json"


SLIDER_X_OFFSET = 50


SLIDER_WIDTH = 182


PROBE_TYPES = {
    1: ("Probe", "probe", 0.04, 3, (238, 120, 224)),
    2: ("Asteroid", "asteroid", 0.01, 3, (170, 135, 100)),
    3: ("Satellite", "moon", 0.001, 2, (180, 190, 205)),
    4: ("Heavy body", "planet", 5.0, 5, (236, 105, 76)),
    5: ("Star", "star", 4500.0, 13, (255, 187, 70)),
}


SCENE_LOCALIZED = {
    "Solar System": "太阳系",
    "Binary Star": "双星",
    "Earth-Moon": "地月",
    "Figure-8": "八字三体",
}


TEXT = {
    "en": {
        "subtitle": "2D orbital sandbox", "simulation": "SIMULATION", "status": "Status",
        "running": "RUNNING", "paused": "PAUSED", "sim_time": "Sim time", "bodies": "Bodies",
        "pause": "Pause", "resume": "Resume", "reset": "Reset", "time_scale": "TIME SCALE",
        "view": "VIEW", "trails": "Trails", "add_body": "Add body", "permanent": "Permanent",
        "follow": "Follow", "scene": "Scene", "selected": "SELECTED BODY",
        "click_body": "Click a body to inspect", "enable_add": "or enable Add body", "energy": "ENERGY",
        "kinetic": "Kinetic", "potential": "Potential", "total": "Total", "drift": "Drift",
        "controls": "CONTROLS", "settings": "Settings", "language": "Language", "english": "English",
        "chinese": "Chinese", "stars": "Starfield", "collisions": "Collision merge", "on": "ON", "off": "OFF",
        "defaults": "Restore defaults", "close": "Close", "delete": "Delete", "settings_title": "SETTINGS",
        "saved": "Settings saved", "labels": "Labels", "probe_type": "Probe type",
        "ctrl_pause": "Space pause / resume", "ctrl_reset": "R reset  T trails",
        "ctrl_follow": "F follow  L labels  C scene", "ctrl_body": "1-5 body type  Ctrl+S/O",
        "no_primary": "N-body scene, no primary", "primary_body": "Primary body", "fixed": "Fixed", "free": "Free",
    },
    "zh": {
        "subtitle": "二维轨道沙盒", "simulation": "模拟状态", "status": "状态",
        "running": "运行中", "paused": "已暂停", "sim_time": "模拟时间", "bodies": "天体数量",
        "pause": "暂停", "resume": "继续", "reset": "重置", "time_scale": "时间倍速",
        "view": "视图", "trails": "轨迹", "add_body": "添加天体", "permanent": "永久轨迹",
        "follow": "跟随", "scene": "场景", "selected": "选中天体",
        "click_body": "点击天体查看信息", "enable_add": "或开启添加模式", "energy": "能量",
        "kinetic": "动能", "potential": "势能", "total": "总能量", "drift": "漂移",
        "controls": "快捷操作", "settings": "设置", "language": "语言", "english": "英文",
        "chinese": "中文", "stars": "星空背景", "collisions": "碰撞合并", "on": "开", "off": "关",
        "defaults": "恢复默认设置", "close": "关闭", "delete": "删除", "settings_title": "设置",
        "saved": "设置已保存", "labels": "标签", "probe_type": "天体类型",
        "ctrl_pause": "空格 暂停/继续", "ctrl_reset": "R 重置  T 轨迹",
        "ctrl_follow": "F 跟随  L 标签  C 场景", "ctrl_body": "1-5 类型  Ctrl+S/O",
        "no_primary": "N 体场景，无主天体", "primary_body": "中心天体", "fixed": "固定", "free": "自由",
    },
}
