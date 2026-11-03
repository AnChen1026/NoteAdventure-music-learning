"""
backend/paths.py｜專案共用路徑

不論從哪個資料夾啟動 Flask，config.ini、uploads/、cache/、material/
都以「專案根目錄」為準，避免換了工作目錄就找不到檔案。
"""

import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)


def project_path(*parts):
    """回傳專案根目錄底下的絕對路徑。"""
    return os.path.join(PROJECT_ROOT, *parts)
