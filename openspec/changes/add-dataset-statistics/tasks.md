## 1. Core Model

- [x] 1.1 Add `DatasetStatistics` model to `packages/search-core/src/grogbot_search/models.py`
- [x] 1.2 Export `DatasetStatistics` from `packages/search-core/src/grogbot_search/__init__.py`

## 2. Service Layer

- [x] 2.1 Implement `statistics(source_id: Optional[str] = None)` method in `SearchService` class
- [x] 2.2 Add unit tests for statistics method in `packages/search-core/tests/test_service.py`

## 3. CLI Interface

- [x] 3.1 Add `statistics` command to `packages/cli/src/grogbot_cli/app.py` under `search_app`

## 4. API Interface

- [x] 4.1 Add `GET /search/statistics` endpoint to `packages/api/src/grogbot_api/app.py`
