## ADDED Requirements

### Requirement: Shared app branding chrome
The system SHALL render the root page, search landing page, and search results page within shared Grogbot branding chrome that includes persistent top-of-page Grogbot branding.

#### Scenario: Root page includes shared branding chrome
- **WHEN** a browser requests `GET /`
- **THEN** the HTML response includes shared Grogbot branding at the top of the page

#### Scenario: Search pages include shared branding chrome
- **WHEN** a browser requests `GET /search` or `GET /search/query?q=hello+world`
- **THEN** the HTML response includes the same shared Grogbot branding at the top of the page

### Requirement: Search result snippets are compact and query-aware
The system SHALL render each search result with a snippet derived from the representative chunk text that is approximately 120 visible characters, prefers to begin near a meaningful literal query-term match when one exists, and appends only a trailing ellipsis when content is truncated.

#### Scenario: Matching term influences snippet start
- **WHEN** a search result chunk contains a meaningful literal query term and the chunk text exceeds the snippet length target
- **THEN** the rendered snippet begins near that query-term match rather than always using the start of the chunk
- **THEN** the rendered snippet is truncated to an approximately 120-character excerpt suitable for compact display

#### Scenario: Non-matching chunk falls back to a clean leading excerpt
- **WHEN** a search result chunk does not contain a meaningful literal query term and the chunk text exceeds the snippet length target
- **THEN** the rendered snippet uses a clean leading excerpt from the chunk text
- **THEN** the rendered snippet appends only a trailing ellipsis when truncated

### Requirement: Visible literal query terms are highlighted in snippets
The system SHALL visually distinguish literal query-term matches that appear in the rendered search-result snippet.

#### Scenario: Matching words are highlighted
- **WHEN** a rendered search-result snippet contains one or more literal query terms from the current search
- **THEN** those visible matched terms are visually highlighted in the HTML response

#### Scenario: No literal match means no highlight
- **WHEN** a rendered search-result snippet contains no literal query terms from the current search
- **THEN** the snippet renders without match-highlighting markup

## MODIFIED Requirements

### Requirement: Grogbot root page
The system SHALL provide an HTML page at `/` that serves as the top-level Grogbot domain entry point and renders within the shared Grogbot branding chrome.

#### Scenario: Root page is available
- **WHEN** a browser requests `GET /`
- **THEN** the system returns an HTML page for the Grogbot root experience
- **THEN** the page renders within the shared Grogbot branding chrome

### Requirement: Search landing page
The system SHALL provide an HTML search landing page at `/search` that renders within the shared Grogbot branding chrome and displays a query input field with a Search submit control in a compact search-first layout.

#### Scenario: Search landing page renders form
- **WHEN** a browser requests `GET /search`
- **THEN** the system returns an HTML page containing a query input field
- **THEN** the page contains a Search submit control
- **THEN** the page renders within the shared Grogbot branding chrome

### Requirement: Search results page
The system SHALL provide an HTML search results page at `/search/query?q=<text>` that renders the top 25 search results for the query within the shared Grogbot branding chrome, includes a query input at the top for running another search, and renders compact result snippets instead of full chunk text.

#### Scenario: Search results page renders ranked results
- **WHEN** a browser requests `GET /search/query?q=hello+world`
- **THEN** the system returns an HTML page containing a query input at the top
- **THEN** the page displays up to 25 ranked search results for `hello world`
- **THEN** each rendered result includes a compact snippet derived from the representative chunk text

#### Scenario: Duplicate documents are preserved in results
- **WHEN** the top 25 ranked search results contain multiple chunks from the same document
- **THEN** the page renders those results in ranked order without deduplicating by document
