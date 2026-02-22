## Context

`@grogbot/alchemist` is a new CLI package that ingests markdown files produced by `@grogbot/goblin`, embeds their content, and stores vectors plus content in a local-file vector database. The implementation must be offline-friendly and rely on LangChainJS for embeddings and vector storage. The embedding model should be configurable via a CLI parameter mapped to a HuggingFace model, defaulting to `Qwen/Qwen3-Embedding-0.6B` using the HuggingFace transformers text embedding interface.

## Goals / Non-Goals

**Goals:**
- Provide a CLI that accepts an input directory of markdown files and ingests all files in batch.
- Use LangChainJS embedding interfaces with HuggingFace transformers, supporting an optional model parameter with default `Qwen/Qwen3-Embedding-0.6B`.
- Store embeddings and post content in LanceDB via the LangChainJS vector store interface.
- Persist a local-file vector database that can be reused across runs.

**Non-Goals:**
- Building a query/search API for the vector database.
- Implementing custom embedding models outside HuggingFace transformers.
- Providing remote or cloud-hosted vector storage.

## Decisions

- **LangChainJS for embeddings and vector store integration.**
  - *Why:* LangChainJS provides standard interfaces for embeddings and vector stores, allowing straightforward integration with HuggingFace transformers and LanceDB.
  - *Alternatives:* Direct HuggingFace SDK usage or custom embedding pipelines; direct LanceDB client without LangChain abstraction.

- **HuggingFace transformers text embedding interface with configurable model name.**
  - *Why:* Enables easy model swapping via CLI, with a sane default model (`Qwen/Qwen3-Embedding-0.6B`) for consistent output.
  - *Alternatives:* Hard-coded model, OpenAI embeddings, or separate config file.

- **LanceDB as the local-file vector database via LangChainJS vector store.**
  - *Why:* LanceDB is optimized for local, file-based vector persistence and has a LangChainJS adapter.
  - *Alternatives:* SQLite-based vector store or in-memory-only storage.

- **Batch ingestion workflow per input directory.**
  - *Why:* Aligns with `@grogbot/goblin` output structure and simplifies operational usage.
  - *Alternatives:* Per-file interactive ingestion or watching for filesystem changes.

## Risks / Trade-offs

- **Model size and performance** → Mitigation: Allow model override via CLI and document resource requirements.
- **Large directories and memory usage** → Mitigation: Stream file processing and upsert incrementally into LanceDB.
- **Dependency weight (LangChainJS + transformers + LanceDB)** → Mitigation: Isolate in new package and ensure clear installation instructions.
