"""Bounded cursor export reference; authentication belongs to the supplied client.

This helper is for endpoints with data[] / pagination.next_cursor. It yields full
receipts, not bare rows. Exhaustion proves only that sequence ended, not exhaustive
semantic recall. Partial pages remain attached to IncompleteCoverage for inspection.
Supply validate_receipt(page) to assert endpoint-specific canonical filter echoes.
The helper cannot infer aliases or identity/geography semantics from request strings.
"""
from copy import deepcopy


class IncompleteCoverage(ValueError):
    def __init__(self, page):
        super().__init__('No positive complete-coverage evidence; inspect the response receipt')
        self.page = page


class PaginationLimit(ValueError):
    def __init__(self, message, page=None):
        super().__init__(message)
        self.page = page


class InvalidReceipt(ValueError):
    def __init__(self, message, page):
        super().__init__(message)
        self.page = page


def cursor_pages(client, path, params, *, max_rows=1000, max_pages=10,
                 page_size=100, require_complete_coverage=True,
                 validate_receipt=None):
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 1
           for value in (max_rows, max_pages, page_size)):
        raise ValueError('Budgets and page size must be positive integers')
    if 'cursor' in params or 'limit' in params:
        raise ValueError('The helper owns cursor and limit; pass page_size separately')
    if validate_receipt is not None and not callable(validate_receipt):
        raise ValueError('validate_receipt must be a callable')
    # Activity binds limit into its cursor fingerprint. Never change it mid-walk,
    # even to use the remainder of a row budget, and freeze caller-owned filters.
    params = deepcopy(params)
    limit = min(page_size, max_rows)
    cursor, seen_cursors, count = None, set(), 0
    page = None
    for _ in range(max_pages):
        if max_rows - count < limit:
            raise PaginationLimit('Remaining row budget cannot fit the unchanged page size; '
                                  'export is incomplete. Increase the budget or start a new walk '
                                  'with a smaller page size.', page)
        query = {**deepcopy(params), 'limit': limit}
        if cursor is not None:
            query['cursor'] = cursor
        response = client.get(path, params=query)
        response.raise_for_status()
        page = response.json()
        if not isinstance(page, dict) or page.get('success') is False:
            raise InvalidReceipt('Unsuccessful or unexpected response receipt', page)
        coverage = (page.get('meta') or {}).get('coverage') or {}
        if require_complete_coverage and coverage.get('window_complete') is not True:
            raise IncompleteCoverage(page)
        applied = page.get('applied_filters') or {}
        if applied.get('ignored'):
            raise InvalidReceipt('The response reported ignored filters; inspect the receipt', page)
        if validate_receipt is not None:
            try:
                validate_receipt(page)
            except ValueError as error:
                raise InvalidReceipt(str(error), page) from error
        rows = page.get('data')
        if not isinstance(rows, list) or len(rows) > limit:
            raise InvalidReceipt('Unexpected row shape or server exceeded requested limit', page)
        pagination = page.get('pagination')
        if not isinstance(pagination, dict) or 'next_cursor' not in pagination:
            raise InvalidReceipt('Not a cursor-pagination response', page)
        next_cursor = pagination['next_cursor']
        if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor):
            raise InvalidReceipt('Unexpected next_cursor; copy only nonempty opaque strings', page)
        if 'has_more' in pagination and (not isinstance(pagination['has_more'], bool)
                                        or pagination['has_more'] != (next_cursor is not None)):
            raise InvalidReceipt('Conflicting pagination receipt; completion is unproven', page)
        if next_cursor is not None and next_cursor in seen_cursors:
            raise PaginationLimit('Cursor did not advance; export is incomplete', page)
        if next_cursor is not None:
            seen_cursors.add(next_cursor)
        count += len(rows)
        yield page
        if next_cursor is None:
            return
        if count >= max_rows:
            raise PaginationLimit('Row budget reached with more available; export is incomplete', page)
        cursor = next_cursor
    raise PaginationLimit('Page budget reached with more available; export is incomplete', page)
