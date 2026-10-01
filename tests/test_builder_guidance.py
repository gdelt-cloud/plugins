"""Exercise the builder examples consumers copy, rather than matching their prose."""
import importlib.util
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'plugins/gdelt-cloud/skills/building-with-the-api/references/details.md'
HELPER = ROOT / 'plugins/gdelt-cloud/skills/building-with-the-api/scripts/cursor_pages.py'
spec = importlib.util.spec_from_file_location('cursor_pages', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def python_examples():
    return re.findall(r'```python\n(.*?)```', REFERENCE.read_text(), re.S)


class ReceiptClient:
    def __init__(self, country):
        self.country, self.calls, self.receipts = country, [], []

    def get(self, path, params):
        self.calls.append((path, params))
        receipt = {
            'success': True, 'data': [], 'pagination': {'next_cursor': None},
            'meta': {'coverage': {'window_complete': True}},
            'applied_filters': {'country': [self.country],
                                **{k: v for k, v in params.items() if k.startswith('date_') or k == 'country_match'}},
            'new_optional_field': None,
        }
        self.receipts.append(receipt)

        class Response:
            def raise_for_status(self):
                pass
            def json(self):
                return receipt

        return Response()


class BuilderGuidanceTest(unittest.TestCase):
    def test_relevance_example_preserves_name_and_unscored_matches(self):
        example = next(block for block in python_examples() if 'search_score' in block)
        rows = [
            {'id': 'name', 'match_type': 'name', 'search_score': None},
            {'id': 'semantic-high', 'match_type': 'semantic', 'search_score': .9},
            {'id': 'semantic-low', 'match_type': 'semantic', 'search_score': .4},
            {'id': 'unscored', 'match_type': 'semantic', 'search_score': None},
        ]
        namespace = {'rows': rows}
        exec(compile(example, str(REFERENCE), 'exec'), namespace)
        output = [row for name, value in namespace.items()
                  if name != 'rows' and isinstance(value, list) for row in value]
        self.assertEqual({row['id'] for row in output}, {row['id'] for row in rows})
        self.assertIsNone(rows[0]['search_score'])
        self.assertIsNone(rows[3]['search_score'])

    def test_copied_cursor_example_checks_the_actual_country_echo(self):
        examples = [block for block in python_examples() if 'validate_receipt=' in block]
        self.assertTrue(examples, 'The cursor example must validate endpoint-specific filter echoes')
        for country in ('FRA', 'USA'):
            with self.subTest(country=country), patch.dict(sys.modules, {'cursor_pages': helper}):
                client = ReceiptClient(country)
                namespace = {'client': client}
                if country == 'USA':
                    with self.assertRaisesRegex(ValueError, 'filter'):
                        exec(compile(examples[0], str(REFERENCE), 'exec'), namespace)
                    self.assertNotIn('pages', namespace)
                else:
                    exec(compile(examples[0], str(REFERENCE), 'exec'), namespace)
                    self.assertEqual(namespace['pages'], client.receipts)
                    self.assertIn('new_optional_field', namespace['pages'][0])
                    params = client.calls[0][1]
                    self.assertEqual(params['country'], 'FRA')
                    self.assertEqual(params['country_match'], 'location')
                    self.assertLess(params['date_start'], params['date_end'])


if __name__ == '__main__':
    unittest.main()
