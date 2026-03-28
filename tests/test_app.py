
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import json
import unittest

from app import BLOCKS_FILE, DATA_FILE, VISA_REGIMES_FILE, app, generate_slots, load_blocks, load_content, load_visa_regimes


class PortalRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.static_map_dir = Path(app.root_path) / 'static' / 'map'
        self.static_images_dir = Path(app.root_path) / 'static' / 'images'
        self.static_docs_dir = Path(app.root_path) / 'static' / 'docs'

    def test_main_content_routes_return_200(self):
        routes = [
            '/', '/laws', '/visa', '/visa/tourist', '/visa/transit', '/visa/work', '/visa/business', '/visa/study',
            '/migration', '/migration/temporary-residence', '/migration/permanent-residence',
            '/migration/citizenship', '/migration/other-status', '/project', '/inside', '/gallery'
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, msg=f'Route failed: {route}')

    def test_citizens_route_is_closed(self):
        self.assertEqual(self.client.get('/citizens').status_code, 404)

    def test_unknown_detail_routes_return_404(self):
        self.assertEqual(self.client.get('/visa/unknown').status_code, 404)
        self.assertEqual(self.client.get('/migration/unknown').status_code, 404)

    def test_navigation_order_matches_requested_structure(self):
        body = self.client.get('/').get_data(as_text=True)
        start = body.index('<nav class="site-nav"')
        end = body.index('</nav>', start)
        nav_html = body[start:end]
        expected = ['Главная', 'Кодексы', 'Визы', 'Легализация', 'О Лососинске', 'Конвертер валют', 'Фотогалерея']
        positions = [nav_html.index(label) for label in expected]
        self.assertEqual(positions, sorted(positions))

    def test_homepage_contains_slider_showcase_and_useful_sections(self):
        body = self.client.get('/').get_data(as_text=True)
        self.assertIn('data-hero-slider', body)
        self.assertIn('Что стоит увидеть в Лососинске', body)
        self.assertIn('Плюсы Лососинска для туризма и жизни', body)
        self.assertIn('Что стоит подготовить заранее', body)
        self.assertIn('Ключевые разделы портала', body)
        self.assertNotIn('Государственные услуги', body)

    def test_visa_overview_uses_tabs_and_regime_widget(self):
        body = self.client.get('/visa').get_data(as_text=True)
        self.assertIn('data-tabs', body)
        self.assertIn('modern-tab', body)
        self.assertIn('visa-panel-tourist', body)
        self.assertIn('Транзитная', body)
        self.assertIn('Подробнее', body)
        self.assertIn('Проверка визового режима по странам', body)
        self.assertIn('data-visa-regime-widget', body)
        self.assertIn('data-regime-search', body)
        self.assertNotIn('JSON-файл', body)

    def test_visa_detail_contains_pdf_and_slot_based_submission(self):
        body = self.client.get('/visa/tourist').get_data(as_text=True)
        self.assertIn('Полный пакет документов', body)
        self.assertIn('Подробнее', body)
        self.assertIn('Запись на подачу', body)
        self.assertIn('Подать', body)
        self.assertNotIn('Открыть форму', body)
        self.assertNotIn('Свободно', body)
        self.assertNotIn('Недоступно', body)
        self.assertNotIn('Занято', body)

    def test_work_visa_detail_contains_categories(self):
        body = self.client.get('/visa/work').get_data(as_text=True)
        self.assertIn('Категория 1', body)
        self.assertIn('Категория 2', body)

    def test_migration_overview_contains_tabs_without_bottom_action_button(self):
        body = self.client.get('/migration').get_data(as_text=True)
        self.assertIn('data-tabs', body)
        self.assertIn('ВНЖ', body)
        self.assertIn('ПМЖ', body)
        self.assertIn('Гражданство', body)
        self.assertIn('Другое', body)
        self.assertIn('Подробнее', body)
        self.assertNotIn('Подать заявку', body)

    def test_migration_detail_contains_pathways_and_pdf(self):
        body = self.client.get('/migration/temporary-residence').get_data(as_text=True)
        self.assertIn('Основания оформления', body)
        self.assertIn('ВНЖ по работе', body)
        self.assertIn('Подробнее', body)
        self.assertIn('Запись на подачу', body)
        self.assertNotIn('Открыть форму', body)

    def test_other_status_uses_request_case_instead_of_regular_slots(self):
        body = self.client.get('/migration/other-status').get_data(as_text=True)
        self.assertIn('Подать запрос кейса', body)
        self.assertIn('Индивидуальное назначение', body)
        self.assertNotIn('Доступные слоты записи', body)

    def test_project_page_mentions_author_server_news_and_map(self):
        body = self.client.get('/project').get_data(as_text=True)
        self.assertIn('карта города', body.lower())
        self.assertIn('Городской Telegram-канал', body)
        self.assertIn('Открыть карту', body)
        self.assertIn('Открыть ТГК', body)
        self.assertNotIn('Постоянные сведения', body)
        self.assertIn('Почему Лососинск удобен для визита, жизни и работы', body)

    def test_inside_page_contains_internal_tabs_and_converter(self):
        body = self.client.get('/inside').get_data(as_text=True)
        self.assertIn('Конвертер валют Лососинска', body)
        self.assertIn('Конвертер валют', body)
        self.assertIn('data-converter-root', body)
        self.assertIn('data-converter-swap', body)
        self.assertIn('За сегодня', body)
        self.assertIn('За месяц', body)
        self.assertIn('За год', body)
        self.assertNotIn('График курса', body)

    def test_content_json_files_exist_and_are_editable(self):
        self.assertTrue(DATA_FILE.exists())
        self.assertTrue(BLOCKS_FILE.exists())
        self.assertTrue(VISA_REGIMES_FILE.exists())
        site_payload = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        blocks_payload = json.loads(BLOCKS_FILE.read_text(encoding='utf-8'))
        self.assertIn('homepage', site_payload)
        self.assertIn('project_page', site_payload)
        self.assertIn('inside_page', site_payload)
        self.assertIn('visas', blocks_payload)
        self.assertIn('migration_types', blocks_payload)
        self.assertIn('inside_state_page', blocks_payload)
        self.assertIn('citizens_page', blocks_payload)
        self.assertIn('showcase_rows', blocks_payload['homepage'])
        self.assertIn('visit_checklist', blocks_payload['homepage'])
        self.assertIn('intro_cards', blocks_payload['inside_state_page'])

    def test_slot_generation_returns_available_slots_close_in_time(self):
        slots = generate_slots('visa-work', 'https://forms.google.com/work-visa', amount=6)
        self.assertGreaterEqual(len(slots), 5)
        self.assertLessEqual(len(slots), 6)
        self.assertTrue(all(slot['audience'] == 'Один заявитель' for slot in slots))
        self.assertTrue(all('forms.google.com/work-visa' in slot['apply_url'] for slot in slots))

    def test_loaders_return_expected_data_and_distinct_form_urls(self):
        site = load_content()
        blocks = load_blocks()
        visa_regimes = load_visa_regimes()
        self.assertEqual(site['site']['title'], 'Портал виз и миграции Лососинска')
        self.assertIn('branding', site['site'])
        self.assertIn('tourist', blocks['visas'])
        self.assertIn('other-status', blocks['migration_types'])
        self.assertEqual(blocks['visas']['tourist']['form_url'], 'https://forms.gle/ZcDgzsDSXwQatweS6')
        self.assertEqual(blocks['visas']['transit']['form_url'], 'https://forms.gle/ZcDgzsDSXwQatweS6')
        self.assertIn('request_form_url', blocks['migration_types']['other-status']['pathways'][0])
        self.assertGreaterEqual(len(visa_regimes), 10)
        self.assertEqual(visa_regimes[0]['country'], 'Тунава')
        self.assertIn('mode', visa_regimes[0])
        self.assertIn('flag', visa_regimes[0])

    def test_required_unmined_map_files_exist(self):
        required = ['index.html', 'index.css', 'unmined.js', 'unmined.map.properties.js', 'unmined.map.regions.js', 'unmined.map.players.js', 'custom.markers.js', 'markers.json']
        for filename in required:
            self.assertTrue((self.static_map_dir / filename).exists(), msg=filename)

    def test_markers_json_contains_required_fields(self):
        payload = json.loads((self.static_map_dir / 'markers.json').read_text(encoding='utf-8'))
        self.assertIn('markers', payload)
        first = payload['markers'][0]
        for key in ['x', 'z', 'title', 'description', 'photos', 'category', 'address', 'openingHours']:
            self.assertIn(key, first)

    def test_hero_and_gallery_images_exist(self):
        for rel in ['hero/hero-01.svg', 'hero/hero-05.svg', 'gallery/gallery-01.svg', 'gallery/gallery-16.svg', 'branding/emblem.svg', 'branding/flag.svg', 'country_flags/tunava.svg']:
            self.assertTrue((self.static_images_dir / rel).exists(), msg=rel)

    def test_pdf_guides_exist_for_visa_and_migration_pages(self):
        required = [
            'visa-tourist-guide.pdf', 'visa-work-guide.pdf', 'visa-business-guide.pdf', 'visa-study-guide.pdf', 'visa-transit-guide.pdf',
            'migration-temporary-residence-guide.pdf', 'migration-permanent-residence-guide.pdf',
            'migration-citizenship-guide.pdf', 'migration-other-status-guide.pdf'
        ]
        for filename in required:
            self.assertTrue((self.static_docs_dir / filename).exists(), msg=filename)


if __name__ == '__main__':
    unittest.main()
