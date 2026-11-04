# ======================================================
# NoteAdventure｜Docker 映像檔
# 第一階段打包 Vue 前端，第二階段只放 Flask 後端 + 打包結果 + 素材
# ======================================================

# ---------- 第一階段：打包 Vue 前端 ----------
FROM node:22.11.0-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- 第二階段：Flask 後端 ----------
FROM python:3.12.7-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY material/ material/
COPY --from=frontend /app/frontend/dist frontend/dist

# 上傳音檔與兩廳院快取放在專案根目錄（compose 會掛 volume 保存）
RUN useradd --create-home appuser \
    && mkdir -p uploads/audio cache \
    && chown -R appuser /app/uploads /app/cache
USER appuser

EXPOSE 5000
# 先確認資料表（與示範資料），再啟動 Flask；雲端平台會用 PORT 指定連接埠
CMD python backend/init_db.py && \
    exec gunicorn --chdir backend -w 2 -b 0.0.0.0:${PORT:-5000} "app:create_app()"
