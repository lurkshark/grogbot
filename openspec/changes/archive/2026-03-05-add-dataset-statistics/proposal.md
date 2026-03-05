## Why

Users need visibility into their search dataset to understand ingestion progress and identify gaps. Currently there's no way to see aggregate counts of sources, documents, chunks, and links, or track embedding progress without manually querying the database.

## What Changes

- Add `DatasetStatistics` model to `search-core` package with counts and computed metrics
- Add `statistics(source_id: Optional[str] = None)` method to `SearchService` returning aggregated dataset metrics
- Add CLI command `grogbot search statistics [--source-id <id>]` to display statistics
- Add API endpoint `GET /search/statistics?source_id=<id>` to retrieve statistics

## Capabilities

### New Capabilities

- `dataset-statistics`: Provides aggregate counts of resources (sources, documents, chunks, links) and embedding progress. Supports optional filtering by source ID to narrow statistics to a specific source.

### Modified Capabilities

None.

## Impact

- **search-core**: New `DatasetStatistics` model in `models.py`, new `statistics()` method in `SearchService`, export in `__init__.py`
- **cli**: New `statistics` command under `search_app` in `app.py`
- **api**: New `GET /search/statistics` endpoint in `app.py`
