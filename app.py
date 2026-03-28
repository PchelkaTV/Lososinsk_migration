from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from flask import Flask, abort, redirect, render_template, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'data' / 'site_content.json'
BLOCKS_FILE = BASE_DIR / 'data' / 'content_blocks.json'
VISA_REGIMES_FILE = BASE_DIR / 'data' / 'visa_regimes.json'

app = Flask(__name__)

NAV_ITEMS = [
    {'endpoint': 'index', 'label': 'Главная'},
    {'endpoint': 'laws', 'label': 'Кодексы'},
    {'endpoint': 'visa', 'label': 'Визы'},
    {'endpoint': 'migration', 'label': 'Легализация'},
    {'endpoint': 'project', 'label': 'О Лососинске'},
    {'endpoint': 'inside', 'label': 'Конвертер валют'},
    {'endpoint': 'gallery', 'label': 'Фотогалерея'},
]

LEGAL_CODES = [
    {'title': 'Конституция Лососинска', 'description': 'Основной закон города-государства.', 'filename': 'constitution-lososinsk.pdf'},
    {'title': 'Уголовный кодекс', 'description': 'Преступления, наказания и меры уголовной ответственности.', 'filename': 'criminal-code.pdf'},
    {'title': 'Уголовно-процессуальный кодекс', 'description': 'Порядок производства по уголовным делам.', 'filename': 'criminal-procedure-code.pdf'},
    {'title': 'Административный кодекс', 'description': 'Составы административных правонарушений и меры взыскания.', 'filename': 'administrative-code.pdf'},
    {'title': 'Кодекс административного судопроизводства', 'description': 'Порядок рассмотрения публично-правовых споров.', 'filename': 'administrative-procedure-code.pdf'},
    {'title': 'Гражданский кодекс', 'description': 'Имущественные, обязательственные и иные гражданско-правовые отношения.', 'filename': 'civil-code.pdf'},
    {'title': 'Гражданско-процессуальный кодекс', 'description': 'Порядок рассмотрения гражданских дел в судах.', 'filename': 'civil-procedure-code.pdf'},
    {'title': 'Семейный кодекс', 'description': 'Брак, семья, родители, дети, опека и попечительство.', 'filename': 'family-code.pdf'},
    {'title': 'Трудовой кодекс', 'description': 'Трудовые права, гарантии и порядок занятости.', 'filename': 'labor-code.pdf'},
    {'title': 'Жилищный кодекс', 'description': 'Пользование жилыми помещениями и жилищные отношения.', 'filename': 'housing-code.pdf'},
    {'title': 'Налоговый кодекс', 'description': 'Налоги, сборы и обязательные публичные платежи.', 'filename': 'tax-code.pdf'},
    {'title': 'Земельный кодекс', 'description': 'Правовой режим земель и территориального использования.', 'filename': 'land-code.pdf'},
]

PROJECT_DOCS = [
    {'title': 'Путеводитель по Лососинску', 'description': 'Краткий вводный PDF по районам, маршрутам и городской логике.', 'filename': 'lososinsk-city-guide.pdf'},
    {'title': 'Карта города', 'description': 'Базовая карта Лососинска для навигации и ориентирования.', 'filename': 'lososinsk-city-map.pdf'},
]

SUPPORTING_DOCS = [
    {'title': 'Общий закон о миграции и статусе иностранных лиц', 'description': 'Регулирование въезда, пребывания, регистрации и прекращения статуса.', 'filename': 'migration-law.pdf'},
    {'title': 'Распоряжения и подзаконные акты', 'description': 'Формы заявлений, административные порядки и подтверждающие документы.', 'filename': 'residence-regulations.pdf'},
]


def load_content() -> dict[str, Any]:
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def load_blocks() -> dict[str, Any]:
    return json.loads(BLOCKS_FILE.read_text(encoding='utf-8'))



def load_visa_regimes() -> list[dict[str, Any]]:
    payload = json.loads(VISA_REGIMES_FILE.read_text(encoding='utf-8'))
    countries = payload['countries']
    mode_map = {
        1: {'label': 'Въезд по визе', 'entry': 'Требуется виза', 'icon': '🛂'},
        2: {'label': 'Электронная виза', 'entry': 'Доступна E-VISA', 'icon': '💻'},
        3: {'label': 'Безвизовый режим', 'entry': 'Виза не требуется', 'icon': '✔'},
        4: {'label': 'Въезд запрещён', 'entry': 'Въезд запрещён', 'icon': '✕'},
    }
    prepared: list[dict[str, Any]] = []
    for item in countries:
        entry = dict(item)
        mode_meta = mode_map.get(entry.get('mode', 1), mode_map[1])
        entry['mode_label'] = mode_meta['label']
        entry['entry_label'] = mode_meta['entry']
        entry['mode_icon'] = mode_meta['icon']
        entry['search_key'] = str(entry.get('country', '')).lower()
        prepared.append(entry)
    return prepared


def doc_url(filename: str) -> str:
    return f'/static/docs/{filename}'


def prepare_documents(items: list[dict[str, Any]], keys: tuple[str, ...] = ('filename',)) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for item in items:
        entry = dict(item)
        for key in keys:
            entry[f'{key}_url'] = doc_url(entry[key])
        prepared.append(entry)
    return prepared


def add_guide_url(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None
    entry = dict(item)
    filename = entry.get('guide_filename')
    if filename:
        entry['guide_url'] = doc_url(filename)
    return entry


def get_visa_types(blocks: dict[str, Any]) -> list[dict[str, Any]]:
    visas = [add_guide_url(item) for item in blocks['visas'].values()]
    visas = [item for item in visas if item]
    visas.sort(key=lambda item: item['display_order'])
    return visas


def get_visa_by_slug(blocks: dict[str, Any], slug: str) -> dict[str, Any] | None:
    item = blocks['visas'].get(slug)
    return add_guide_url(item)


def get_migration_types(blocks: dict[str, Any]) -> list[dict[str, Any]]:
    items = [add_guide_url(item) for item in blocks['migration_types'].values()]
    items = [item for item in items if item]
    items.sort(key=lambda item: item['display_order'])
    return items


def get_migration_by_slug(blocks: dict[str, Any], slug: str) -> dict[str, Any] | None:
    item = blocks['migration_types'].get(slug)
    return add_guide_url(item)


def generate_slots(kind: str, apply_base_url: str, amount: int = 6) -> list[dict[str, Any]]:
    now = datetime.now().replace(second=0, microsecond=0)
    rnd = random.Random(f"{kind}-{now:%Y%m%d}")
    total = rnd.randint(max(4, amount - 1), amount)
    day_offsets = sorted(rnd.sample(range(1, 9), k=total))
    hour_pool = [9, 10, 11, 12, 13, 14, 15, 16]
    minute_pool = [0, 15, 30, 45]
    slots: list[dict[str, Any]] = []
    for day in day_offsets:
        slot_dt = (now + timedelta(days=day)).replace(hour=rnd.choice(hour_pool), minute=rnd.choice(minute_pool))
        separator = '&' if '?' in apply_base_url else '?'
        slots.append(
            {
                'label': slot_dt.strftime('%d.%m.%Y · %H:%M'),
                'audience': 'Один заявитель',
                'apply_url': f"{apply_base_url}{separator}slot={quote(slot_dt.isoformat())}",
            }
        )
    return slots




def generate_lorin_market() -> dict[str, Any]:
    fallback_eur_rates = {
        'EUR': 1.0,
        'USD': 1.1517,
        'RUB': 95.0038,
        'RSD': 117.4403,
        'TRY': 51.2001,
        'CNY': 7.9737,
    }

    def fetch_live_eur_rates() -> dict[str, float]:
        try:
            with urlopen('https://open.er-api.com/v6/latest/EUR', timeout=4) as response:
                payload = json.loads(response.read().decode('utf-8'))
            rates = payload.get('rates', {})
            required = {'USD', 'RUB', 'RSD', 'TRY', 'CNY'}
            if not required.issubset(rates):
                return fallback_eur_rates
            return {
                'EUR': 1.0,
                'USD': float(rates['USD']),
                'RUB': float(rates['RUB']),
                'RSD': float(rates['RSD']),
                'TRY': float(rates['TRY']),
                'CNY': float(rates['CNY']),
            }
        except Exception:
            return fallback_eur_rates

    eur_rates = fetch_live_eur_rates()

    # 1 EUR ~= 0.81 LOR with a very small deterministic drift.
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    day_seed = now.timetuple().tm_yday
    hour_seed = now.hour
    eur_to_lor = 0.81 + math.sin(day_seed / 18.0) * 0.004 + math.cos(hour_seed / 5.0) * 0.0015
    eur_to_lor = round(max(0.798, min(0.822, eur_to_lor)), 5)

    profiles = {
        'LOR': {'label': 'Лорин', 'symbol': 'Ł', 'vol': (0.12, 0.7, 1.6)},
        'EUR': {'label': 'Евро', 'symbol': '€', 'vol': (0.18, 1.0, 2.4)},
        'PIS': {'label': 'Пискат', 'symbol': '₣', 'vol': (0.18, 1.0, 2.4)},
        'USD': {'label': 'Доллар США', 'symbol': '$', 'vol': (0.55, 3.8, 7.2)},
        'RUB': {'label': 'Российский рубль', 'symbol': '₽', 'vol': (1.9, 9.5, 18.0)},
        'RSD': {'label': 'Сербский динар', 'symbol': 'дин', 'vol': (0.35, 1.9, 4.2)},
        'TRY': {'label': 'Турецкая лира', 'symbol': '₺', 'vol': (2.4, 11.5, 24.0)},
        'CNY': {'label': 'Китайский юань', 'symbol': '¥', 'vol': (0.45, 2.8, 5.8)},
    }

    def to_lor(code: str) -> float:
        if code == 'LOR':
            return 1.0
        if code == 'PIS':
            return eur_to_lor
        if code == 'EUR':
            return eur_to_lor
        return eur_to_lor / eur_rates[code]

    current_rates = {code: round(to_lor(code), 6) for code in profiles}

    def synthetic_change(code: str, period: str) -> float:
        bounds = profiles[code]['vol']
        idx = {'today': 0, 'month': 1, 'year': 2}[period]
        amp = bounds[idx]
        base = (math.sin((day_seed / (7 + idx * 5)) + len(code) * 0.61) + math.cos((hour_seed / (3.5 + idx)) + len(code) * 0.37)) * 0.5
        rnd = random.Random(f'{code}-{period}-{now:%Y%m%d%H}')
        jitter = rnd.uniform(-0.35, 0.35)
        value = (base + jitter) * amp
        return round(value, 2)

    snapshots: dict[str, dict[str, float]] = {}
    for period in ('today', 'month', 'year'):
        period_snapshot = {}
        for code, current in current_rates.items():
            pct = synthetic_change(code, period)
            divisor = 1 + (pct / 100.0)
            if abs(divisor) < 0.0001:
                divisor = 1.0
            period_snapshot[code] = round(current / divisor, 6)
        snapshots[period] = period_snapshot

    currencies = []
    for code, spec in profiles.items():
        current = current_rates[code]
        currencies.append({
            'code': code,
            'label': spec['label'],
            'symbol': spec['symbol'],
            'to_lorin': current,
            'from_lorin': round(1 / current, 6) if current else 0.0,
        })

    snapshot = {
        'currencies': currencies,
        'reference_pair': f'1 EUR = {eur_to_lor:.4f} LOR',
    }
    payload = {
        'currencies': currencies,
        'current_rates': current_rates,
        'snapshots': snapshots,
    }
    return {'snapshot': snapshot, 'payload': payload}

def base_context(page_title: str) -> dict[str, Any]:
    content = load_content()
    blocks = load_blocks()
    return {
        'site': content['site'],
        'content_data': content,
        'blocks_data': blocks,
        'nav_items': NAV_ITEMS,
        'page_title': page_title,
    }


@app.route('/')
def index():
    context = base_context('Главная')
    content = context['content_data']
    blocks = context['blocks_data']
    context.update(
        homepage=content['homepage'],
        homepage_sections=content['homepage_sections'],
        homepage_blocks=blocks['homepage'],
    )
    return render_template('index.html', **context)


@app.route('/visa')
def visa():
    context = base_context('Виза')
    content = context['content_data']
    visa_types = get_visa_types(context['blocks_data'])
    context.update(
        visa_page=content['visa_page'],
        visa_types=visa_types,
        visa_regimes=load_visa_regimes(),
    )
    return render_template('visa.html', **context)


@app.route('/visa/<slug>')
def visa_detail(slug: str):
    context = base_context('Виза')
    content = context['content_data']
    visa_item = get_visa_by_slug(context['blocks_data'], slug)
    if visa_item is None:
        abort(404)

    context.update(
        visa_item=visa_item,
        visa_page=content['visa_page'],
        appointment_slots=generate_slots(f'visa-{slug}', visa_item['form_url']),
    )
    return render_template('visa_detail.html', **context)


@app.route('/laws')
def laws():
    context = base_context('Кодексы')
    context.update(legal_codes=prepare_documents(LEGAL_CODES))
    return render_template('laws.html', **context)


@app.route('/migration')
def migration():
    context = base_context('Легализация')
    content = context['content_data']
    blocks = context['blocks_data']
    migration_types = get_migration_types(blocks)
    context.update(
        migration_page=content['migration_page'],
        migration_types=migration_types,
        supporting_docs=prepare_documents(SUPPORTING_DOCS),
    )
    return render_template('migration.html', **context)


@app.route('/migration/<slug>')
def migration_detail(slug: str):
    context = base_context('Легализация')
    content = context['content_data']
    migration_item = get_migration_by_slug(context['blocks_data'], slug)
    if migration_item is None:
        abort(404)

    context.update(
        migration_page=content['migration_page'],
        migration_item=migration_item,
        supporting_docs=prepare_documents(SUPPORTING_DOCS),
        appointment_slots=generate_slots(f'migration-{slug}', migration_item['form_url']) if slug != 'other-status' else [],
    )
    return render_template('migration_detail.html', **context)


@app.route('/project')
def project():
    context = base_context('О Лососинске')
    content = context['content_data']
    blocks = context['blocks_data']
    context.update(
        project_page=content['project_page'],
        project_blocks=blocks['project_page'],
        project_docs=prepare_documents(PROJECT_DOCS),
    )
    return render_template('project.html', **context)






@app.route('/inside')
def inside():
    context = base_context('Конвертер валют')
    content = context['content_data']
    blocks = context['blocks_data']
    market = generate_lorin_market()
    context.update(
        inside_page=content['inside_page'],
        inside_blocks=blocks['inside_state_page'],
        market_snapshot=market['snapshot'],
        market_payload=market['payload'],
    )
    return render_template('inside.html', **context)

@app.route('/gallery')
def gallery():
    context = base_context('Фотогалерея')
    content = context['content_data']
    blocks = context['blocks_data']
    context.update(gallery_page=content['gallery_page'], gallery_items=blocks['gallery']['items'])
    return render_template('gallery.html', **context)


@app.route('/citizens')
def citizens():
    abort(404)


@app.route('/map')
def map_page():
    return redirect(url_for('static', filename='map/index.html'))


if __name__ == '__main__':
    app.run(debug=False)
