# 明天到公司部署：最短檢查表

如果主機可以用 Docker，優先走 Docker；如果不方便，再走 Ubuntu 原生模式。

## Docker 路線

```bash
git clone https://github.com/linjose/ix3-TMT.git
cd ix3-TMT
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
nano .env
```

`.env` 至少改：

```dotenv
DJANGO_SECRET_KEY=<random>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=<主機IP>,127.0.0.1,localhost
DB_PASSWORD=<strong password>
```

然後：

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py tmt_check
docker compose ps
docker compose logs --tail=100 worker
```

瀏覽：

```text
http://主機IP:8000/
```

登入後先上傳一份 3–10 頁測試 PPTX，然後：

```bash
docker compose logs -f worker
```

確認 Deck 從：

```text
排程中 → 處理中 → 可使用
```

最後測：

- 首頁出現每頁 Slide。
- PPT 文字可搜尋。
- 截圖型 Slide 的 OCR 字可搜尋。
- Star 數增加。
- 建 Collection 並加入 Slide。
- `/admin/` 可以看到 ProcessingJob。

## 原生 Ubuntu 路線

```bash
sudo ./scripts/install_ubuntu.sh
cp .env.example .env
nano .env
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py tmt_check
```

Terminal A：

```bash
python manage.py runserver 0.0.0.0:8000
```

Terminal B：

```bash
python manage.py process_jobs --loop --poll-seconds 30
```

先確認功能，再決定是否改 PostgreSQL + Systemd + Nginx。

## 若當天只想先 Demo

可以先用：

```dotenv
DB_HOST=
DJANGO_DEBUG=1
```

也就是 SQLite，不必先處理 PostgreSQL。核心 PPT/OCR 功能仍然可用。
