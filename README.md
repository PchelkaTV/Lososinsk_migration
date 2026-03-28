# Государственный портал Лососинска

Локальный многостраничный Flask-проект с отдельной картой uNmINeD, фотогалереей, разделом кодексов, визами, легализацией и заготовкой блока государственных услуг.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Открой `http://127.0.0.1:5000`.

## Структура

- `app.py` — маршруты, загрузка JSON-контента и генерация доступных слотов.
- `data/site_content.json` — короткие тексты страниц, заголовки, лиды, подписи разделов.
- `data/content_blocks.json` — большие блоки: главная, карточки виз, статусы, основания, проект, галерея, госуслуги.
- `templates/` — HTML-шаблоны сайта.
- `static/css/style.css` — единый адаптивный стиль сайта.
- `static/docs/` — кодексы, путеводитель и PDF-гайды по визам и легализации.
- `static/images/hero/` — изображения для главного слайдера и городских блоков.
- `static/images/gallery/` — изображения фотогалереи.
- `static/map/` — отдельная полноэкранная карта и её данные.
- `tests/test_app.py` — базовые тесты маршрутов и структуры данных.

## Что менять в первую очередь

- ссылки на Telegram и Wiki — в `data/site_content.json`
- большие тексты и основания оформления — в `data/content_blocks.json`
- изображения главной и галереи — в `static/images/hero/` и `static/images/gallery/`
- PDF-документы — в `static/docs/`
- карта и маркеры — в `static/map/`
