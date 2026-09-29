"""Bounded cursor export reference; authentication belongs to the supplied client.

This helper is for endpoints with data[] / pagination.next_cursor. It yields full
receipts, not bare rows. Exhaustion proves only that sequence ended, not exhaustive
semantic recall. Partial pages remain attached to IncompleteCoverage for inspection.
"""


class IncompleteCoverage(ValueError):
    def __init__(self, page):
        super().__init__('No positive complete-coverage evidence; inspect the response receipt')
        self.page = page


class PaginationLimit(ValueError):
    pass


def cursor_pages(client, path, params, *, max_rows=1000, max_pages=10,
                 page_size=100, require_complete_coverage=True):
    if min(max_rows, max_pages, page_size) < 1:
        raise ValueError('Budgets and page size must be positive')
    if 'cursor' in params or 'limit' in params:
        raise ValueError('The helper owns cursor and limit; pass page_size separately')
    cursor, seen_cursors, count = None, set(), 0
    for _ in range(max_pages):
        limit = min(page_size, max_rows - count)
        query = {**params, 'limit': limit}
        if cursor is not None:
            query['cursor'] = cursor
        response = client.get(path, params=query)
        response.raise_for_status()
        page = response.json()
        coverage = (page.get('meta') or {}).get('coverage') or {}
        if require_complete_coverage and coverage.get('window_complete') is not True:
            raise IncompleteCoverage(page)
        rows = page['data']
        if not isinstance(rows, list) or len(rows) > limit:
            raise ValueError('Unexpected row shape or server exceeded requested limit')
        pagination = page['pagination']
        if 'next_cursor' not in pagination:
            raise ValueError('Not a cursor-pagination response')
        next_cursor = pagination['next_cursor']
        count += len(rows)
        yield page
        if next_cursor is None:
            return
        if next_cursor in seen_cursors:
            raise PaginationLimit('Cursor did not advance; export is incomplete')
        seen_cursors.add(next_cursor)
        if count >= max_rows:
            raise PaginationLimit('Row budget reached with more available; export is incomplete')
        cursor = next_cursor
    raise PaginationLimit('Page budget reached with more available; export is incomplete')
