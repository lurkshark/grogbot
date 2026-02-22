import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import test from "node:test";
import assert from "node:assert/strict";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function mockEmbeddings({ modelName } = {}) {
  return {
    embedDocuments: async (texts) => texts.map(() => [0.1, 0.2, 0.3]),
    embedQuery: async () => [0.1, 0.2, 0.3],
    modelName,
  };
}

function mockVectorStore() {
  const calls = [];
  return {
    addDocuments: async (documents) => {
      calls.push(...documents);
    },
    getCalls: () => calls,
  };
}

async function setupInputDir() {
  const tempDir = await mkdtemp(path.join(__dirname, "fixtures-"));
  await writeFile(path.join(tempDir, "post-a.md"), "# Post A\nHello A");
  await writeFile(path.join(tempDir, "post-b.md"), "# Post B\nHello B");
  await writeFile(path.join(tempDir, "notes.txt"), "Ignore me");
  return tempDir;
}

test("ingestDirectory processes markdown files and persists documents", async () => {
  const { ingestDirectory, __test__ } = await import("../dist/ingest.js");

  const inputDir = await setupInputDir();
  const vectorStore = mockVectorStore();
  const embeddings = mockEmbeddings({ modelName: "mock/model" });

  try {
    __test__.setVectorStoreFactory(async () => vectorStore);
    __test__.setEmbeddingsFactory(() => embeddings);

    const summary = await ingestDirectory({
      inputDir,
      modelName: "mock/model",
    });

    assert.equal(summary.processed, 2);
    assert.equal(summary.skipped, 1);
    assert.equal(summary.errors, 0);
    assert.equal(vectorStore.getCalls().length, 2);
  } finally {
    __test__.resetFactories();
    await rm(inputDir, { recursive: true, force: true });
  }
});

test("CLI defaults to Qwen embedding model when omitted", async () => {
  const { run } = await import("../dist/command.js");
  const { __test__ } = await import("../dist/ingest.js");

  const inputDir = await setupInputDir();

  try {
    let capturedModel = null;
    __test__.setEmbeddingsFactory((modelName) => {
      capturedModel = modelName;
      return mockEmbeddings({ modelName });
    });
    __test__.setVectorStoreFactory(async () => mockVectorStore());

    await run(["ingest", inputDir]);

    assert.equal(capturedModel, "Qwen/Qwen3-Embedding-0.6B");
  } finally {
    __test__.resetFactories();
    await rm(inputDir, { recursive: true, force: true });
  }
});

test("ingestDirectory reuses consistent LanceDB path", async () => {
  const { ingestDirectory, __test__ } = await import("../dist/ingest.js");

  const inputDir = await setupInputDir();
  const vectorStore = mockVectorStore();
  const embeddings = mockEmbeddings({ modelName: "mock/model" });

  try {
    __test__.setVectorStoreFactory(async () => vectorStore);
    __test__.setEmbeddingsFactory(() => embeddings);

    const first = await ingestDirectory({
      inputDir,
      modelName: "mock/model",
    });
    const second = await ingestDirectory({
      inputDir,
      modelName: "mock/model",
    });

    assert.equal(first.dbPath, second.dbPath);
  } finally {
    __test__.resetFactories();
    await rm(inputDir, { recursive: true, force: true });
  }
});
