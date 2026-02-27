## ADDED Requirements

### Requirement: Create document from URL
The core SHALL provide `createDocumentFromURL` that fetches a URL, extracts main content with `python-readability`, converts it to markdown, and upserts a Document with metadata derived from the page.

#### Scenario: URL ingestion creates a document
- **WHEN** `createDocumentFromURL` is called with a valid URL
- **THEN** a Document is created or updated with markdown content and extracted metadata

### Requirement: Auto-create Source for URL ingestion
When ingesting a URL, if no Source exists for the canonical domain (full host), the system MUST create one automatically.

#### Scenario: Source auto-creation
- **WHEN** a URL is ingested from a new canonical domain
- **THEN** a Source is created for that domain and linked to the Document

### Requirement: Create documents from RSS feed
The core SHALL provide `createDocumentsFromFeed` that fetches and parses an RSS/Atom feed, converts `content:encoded` HTML to markdown, and creates or updates a Document per entry using the canonical URL and entry metadata.

#### Scenario: Feed ingestion creates multiple documents
- **WHEN** `createDocumentsFromFeed` processes a feed with multiple entries
- **THEN** a Document is created or updated for each unique canonical URL

### Requirement: Canonical URL handling
For URL and feed ingestion, the system MUST determine a canonical URL using explicit canonical links when present, otherwise using the original entry URL, and MUST enforce a single Document per canonical URL.

#### Scenario: Duplicate URL ingestion
- **WHEN** the same canonical URL is ingested multiple times
- **THEN** only one Document exists and subsequent ingestions update it
