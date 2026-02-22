import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { HuggingFaceTransformersEmbeddings } from "@langchain/community/embeddings/hf_transformers";
import { LanceDB } from "@langchain/community/vectorstores/lancedb";
import { Document } from "@langchain/core/documents";
import { connect } from "@lancedb/lancedb";

export type IngestOptions = {
  inputDir: string;
  modelName: string;
};

export type IngestSummary = {
  processed: number;
  skipped: number;
  errors: number;
  dbPath: string;
  tableName: string;
};

const DEFAULT_TABLE = "markdown_posts";

export async function ingestDirectory(options: IngestOptions): Promise<IngestSummary> {
  const inputDir = path.resolve(options.inputDir);
  const dbPath = path.resolve(process.cwd(), "lancedb");
  const tableName = DEFAULT_TABLE;

  const embeddings = embeddingsFactory(options.modelName);

  const vectorStore = await vectorStoreFactory({
    embeddings,
    dbPath,
    tableName,
  });

  const entries = await readdir(inputDir, { withFileTypes: true });
  const markdownFiles = entries.filter(
    (entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".md")
  );

  let processed = 0;
  let skipped = 0;
  let errors = 0;

  for (const entry of markdownFiles) {
    const filePath = path.join(inputDir, entry.name);
    try {
      const content = await readFile(filePath, "utf8");
      const document = new Document({
        pageContent: content,
        metadata: {
          source: filePath,
          filename: entry.name,
        },
      });

      await vectorStore.addDocuments([document]);
      processed += 1;
    } catch (error) {
      errors += 1;
      console.error(
        `Failed to ingest ${entry.name}: ${error instanceof Error ? error.message : error}`
      );
    }
  }

  skipped = entries.length - markdownFiles.length;

  if (processed === 0 && markdownFiles.length === 0) {
    console.warn(`No markdown files found in ${inputDir}.`);
  }

  return {
    processed,
    skipped,
    errors,
    dbPath,
    tableName,
  };
}

type VectorStoreOptions = {
  embeddings: HuggingFaceTransformersEmbeddings;
  dbPath: string;
  tableName: string;
};

type EmbeddingsFactory = (modelName: string) => HuggingFaceTransformersEmbeddings;

let embeddingsFactory: EmbeddingsFactory = (modelName) =>
  new HuggingFaceTransformersEmbeddings({
    modelName,
  });

let vectorStoreFactory = async (options: VectorStoreOptions): Promise<LanceDB> => {
  const connection = (await connect(options.dbPath)) as any;
  let table: any;

  try {
    table = await connection.openTable(options.tableName);
  } catch {
    table = await connection.createTable(options.tableName, []);
  }

  return new LanceDB(options.embeddings, {
    table,
  });
};

export const __test__ = {
  setEmbeddingsFactory(factory: EmbeddingsFactory): void {
    embeddingsFactory = factory;
  },
  setVectorStoreFactory(factory: typeof vectorStoreFactory): void {
    vectorStoreFactory = factory;
  },
  resetFactories(): void {
    embeddingsFactory = (modelName) =>
      new HuggingFaceTransformersEmbeddings({
        modelName,
      });
    vectorStoreFactory = async (options: VectorStoreOptions): Promise<LanceDB> => {
      const connection = (await connect(options.dbPath)) as any;
      let table: any;

      try {
        table = await connection.openTable(options.tableName);
      } catch {
        table = await connection.createTable(options.tableName, []);
      }

      return new LanceDB(options.embeddings, {
        table,
      });
    };
  },
};
