import { parseArgs } from "node:util";
import { ingestDirectory } from "./ingest.js";

const DEFAULT_MODEL = "Xenova/all-MiniLM-L6-v2";

const USAGE = "alchemist ingest <dir> [--model <name>]";

type ParsedArgs = {
  values: {
    model?: string;
  };
  positionals: string[];
};

export async function run(argv: string[]): Promise<void> {
  const [command, ...rest] = argv;
  if (!command || command === "--help" || command === "-h") {
    printUsage();
    return;
  }

  if (command !== "ingest") {
    throw new Error(`Unknown command: ${command}`);
  }

  const parsed = parseArgs({
    args: rest,
    allowPositionals: true,
    options: {
      model: {
        type: "string",
        short: "m",
      },
    },
  }) as ParsedArgs;

  const inputDir = parsed.positionals[0];
  if (!inputDir) {
    throw new Error("Missing input directory.");
  }

  const modelName = parsed.values.model ?? DEFAULT_MODEL;

  const summary = await ingestDirectory({
    inputDir,
    modelName,
  });

  console.log(
    `Ingested ${summary.processed} markdown files into LanceDB at ${summary.dbPath}.`
  );
}

function printUsage(): void {
  console.log(USAGE);
}
