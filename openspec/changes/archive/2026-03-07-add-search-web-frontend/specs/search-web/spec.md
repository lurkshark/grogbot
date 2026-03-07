## ADDED Requirements

### Requirement: Grogbot root page
The system SHALL provide an HTML page at `/` that serves as the top-level Grogbot domain entry point.

#### Scenario: Root page is available
- **WHEN** a browser requests `GET /`
- **THEN** the system returns an HTML page for the Grogbot root experience

### Requirement: Search landing page
The system SHALL provide an HTML search landing page at `/search` that displays the title "Grogbot Search", a text input for the query, and a Search submit control.

#### Scenario: Search landing page renders form
- **WHEN** a browser requests `GET /search`
- **THEN** the system returns an HTML page containing the text "Grogbot Search"
- **THEN** the page contains a query input field
- **THEN** the page contains a Search submit control

### Requirement: Search results page
The system SHALL provide an HTML search results page at `/search/query?q=<text>` that renders the top 25 search results for the query and includes a query input at the top for running another search.

#### Scenario: Search results page renders ranked results
- **WHEN** a browser requests `GET /search/query?q=hello+world`
- **THEN** the system returns an HTML page containing a query input at the top
- **THEN** the page displays up to 25 ranked search results for `hello world`

#### Scenario: Duplicate documents are preserved in v1 results
- **WHEN** the top 25 ranked search results contain multiple chunks from the same document
- **THEN** the page renders those results in ranked order without deduplicating by document

### Requirement: Empty search redirects to landing page
The system SHALL redirect requests for `/search/query` without a non-blank `q` parameter to `/search`.

#### Scenario: Missing query redirects to search landing
- **WHEN** a browser requests `GET /search/query` without a `q` parameter
- **THEN** the system responds with a redirect to `/search`

#### Scenario: Blank query redirects to search landing
- **WHEN** a browser requests `GET /search/query?q=   `
- **THEN** the system responds with a redirect to `/search`
