"""公共 fixture — 将项目根目录加入 sys.path，便于 import 各模块。"""
import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
