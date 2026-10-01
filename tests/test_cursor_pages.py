import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'plugins/gdelt-cloud/skills/building-with-the-api/scripts/cursor_pages.py'
spec = importlib.util.spec_from_file_location('cursor_pages', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def page(rows, cursor=None, complete=True):
    return {'data': rows, 'pagination': {'next_cursor': cursor},
            'meta': {'coverage': {'window_complete': complete}}, 'applied_filters': {'country': 'Iran'}}


class Client:
    def __init__(self, pages, error=None):
        self.pages, self.calls, self.error = iter(pages), [], error

    def get(self, path, params):
        self.calls.append((path, params))
        value, error = next(self.pages), self.error
        class Response:
            def raise_for_status(self):
                if error:
                    raise error
            def json(self):
                return value
        return Response()


class CursorPagesTest(unittest.TestCase):
    def test_budget_limits_request_and_discloses_remaining(self):
        c = Client([page([1, 2, 3], 'next')])
        pages = m.cursor_pages(c, '/events', {}, max_rows=3)
        self.assertEqual(next(pages)['data'], [1, 2, 3])
        with self.assertRaises(m.PaginationLimit): next(pages)
        self.assertEqual(c.calls[0][1]['limit'], 3)
        self.assertEqual(len(c.calls), 1)

    def test_missing_or_partial_coverage_is_not_empty_success(self):
        for complete in (False, None):
            with self.assertRaises(m.IncompleteCoverage) as caught:
                list(m.cursor_pages(Client([page([], complete=complete)]), '/events', {}))
            self.assertEqual(caught.exception.page['data'], [])

    def test_receipts_and_opaque_cursor_are_preserved(self):
        first, last = page([1], 'opaque=='), page([2])
        c = Client([first, last])
        self.assertEqual(list(m.cursor_pages(c, '/events', {'country':'Iran'})), [first, last])
        self.assertEqual(c.calls[1][1]['cursor'], 'opaque==')
        self.assertEqual(c.calls[1][1]['country'], 'Iran')

    def test_repeated_cursor_and_call_budget_stop(self):
        for options in ({}, {'max_pages':1}):
            c = Client([page([], 'same'), page([], 'same')])
            with self.assertRaises(m.PaginationLimit): list(m.cursor_pages(c, '/events', {}, **options))
            self.assertLessEqual(len(c.calls), 2)

    def test_http_failure_is_not_success_json(self):
        with self.assertRaisesRegex(RuntimeError, 'quota'):
            list(m.cursor_pages(Client([{}], RuntimeError('quota')), '/events', {}))

    def test_non_cursor_shape_and_oversized_page_rejected(self):
        for value in ({'data':[], 'pagination':{'offset':0}}, page([1,2])):
            with self.assertRaises(ValueError):
                list(m.cursor_pages(Client([value]), '/events', {}, max_rows=1,
                                    require_complete_coverage=False))

    def test_row_budget_never_changes_a_cursor_bound_page_size(self):
        c = Client([page([1, 2], 'opaque'), page([3])])
        pages = m.cursor_pages(c, '/activity', {}, page_size=2, max_rows=3)
        self.assertEqual(next(pages)['data'], [1, 2])
        with self.assertRaises(m.PaginationLimit):
            next(pages)
        # Activity fingerprints limit too. A smaller continuation is a different query.
        self.assertEqual([query['limit'] for _, query in c.calls], [2])

    def test_caller_mutation_cannot_change_the_frozen_query(self):
        params = {'country': 'Iran'}
        c = Client([page([1], 'opaque'), page([2])])
        pages = m.cursor_pages(c, '/events', params)
        next(pages)
        params['country'] = 'France'
        next(pages)
        self.assertEqual(c.calls[1][1]['country'], 'Iran')

    def test_explicit_ignored_filters_are_not_a_valid_receipt(self):
        value = page([])
        value['applied_filters']['ignored'] = ['country']
        with self.assertRaisesRegex(ValueError, 'ignored filters') as caught:
            next(m.cursor_pages(Client([value]), '/events', {'country': 'Iran'}))
        self.assertIs(caught.exception.page, value)

    def test_malformed_cursor_is_rejected_before_a_page_is_yielded(self):
        for cursor in ('', 123, [], {}):
            with self.subTest(cursor=cursor), self.assertRaisesRegex(ValueError, 'cursor'):
                next(m.cursor_pages(Client([page([], cursor)]), '/activity', {}))

    def test_conflicting_pagination_cannot_establish_completion(self):
        for cursor, more in ((None, True), ('opaque', False), (None, 'false')):
            value = page([], cursor)
            value['pagination']['has_more'] = more
            with self.subTest(cursor=cursor, more=more), self.assertRaisesRegex(ValueError, 'pagination'):
                next(m.cursor_pages(Client([value]), '/activity', {}))

    def test_repeated_cursor_is_rejected_before_the_repeated_page_is_yielded(self):
        c = Client([page([1], 'same'), page([2], 'same')])
        pages = m.cursor_pages(c, '/events', {})
        self.assertEqual(next(pages)['data'], [1])
        with self.assertRaises(m.PaginationLimit) as caught:
            next(pages)
        self.assertEqual(caught.exception.page['data'], [2])

    def test_endpoint_receipt_validator_rejects_changed_semantic_filters(self):
        value = page([])
        value['applied_filters'] = {'country': 'USA'}

        def validate(receipt):
            if receipt['applied_filters'].get('country') != 'FRA':
                raise ValueError('Country filter changed')

        with self.assertRaisesRegex(ValueError, 'Country filter changed') as caught:
            next(m.cursor_pages(Client([value]), '/events', {'country': 'FRA'},
                                validate_receipt=validate))
        self.assertIs(caught.exception.page, value)

    def test_validated_complete_empty_page_preserves_unknown_receipt_fields(self):
        value = page([])
        value['applied_filters'] = {'country': 'FRA'}
        value['meta']['exhaustive'] = False
        value['future_optional_field'] = {'unmeasured': None}
        seen = []

        def validate(receipt):
            seen.append(receipt)
            if receipt['applied_filters']['country'] != 'FRA':
                raise ValueError('Country filter changed')

        self.assertEqual(list(m.cursor_pages(Client([value]), '/events', {'country': 'FRA'},
                                             validate_receipt=validate)), [value])
        self.assertEqual(seen, [value])


if __name__ == '__main__': unittest.main()
