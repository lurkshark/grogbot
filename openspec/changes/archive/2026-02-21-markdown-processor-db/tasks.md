## 1. Package Setup

- [x] 1.1 Create new package directory `packages/alchemist` with CLI entrypoint skeleton
- [x] 1.2 Add package metadata, scripts, and dependencies for LangChainJS, HuggingFace transformers embeddings, and LanceDB

## 2. CLI Inputs and Configuration

- [x] 2.1 Parse CLI arguments for input directory and optional embedding model parameter
- [x] 2.2 Implement default model selection (`Qwen/Qwen3-Embedding-0.6B`) when parameter is omitted

## 3. Embeddings and Vector Store Integration

- [x] 3.1 Wire LangChainJS HuggingFace transformers embeddings with model name from CLI
- [x] 3.2 Initialize or connect to local LanceDB instance using LangChainJS vector store

## 4. Markdown Ingestion Workflow

- [x] 4.1 Discover `.md` files in the input directory and iterate in batch
- [x] 4.2 Load markdown file content and generate embeddings for each file
- [x] 4.3 Persist vectors and associated post content to LanceDB per file

## 5. Persistence and Reuse

- [x] 5.1 Ensure LanceDB storage is reused across runs (consistent local path)
- [x] 5.2 Add basic logging/error handling for ingestion summary
