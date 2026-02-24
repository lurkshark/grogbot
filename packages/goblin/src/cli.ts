#!/usr/bin/env node
import { Command } from 'commander';
import { runIngest } from './commands/ingest.js';
import { runExtract } from './commands/extract.js';
import { runStore } from './commands/store.js';

const program = new Command();

program
  .name('goblin')
  .description('RSS ingest, LLM extract, and storage pipeline for Grogbot.')
  .showHelpAfterError();

program
  .command('ingest')
  .description('Ingest an RSS feed into pond/ingest.')
  .argument('<pond>', 'Path to pond directory')
  .argument('<feedUrl>', 'RSS feed URL')
  .action(async (pond: string, feedUrl: string) => {
    try {
      await runIngest(pond, feedUrl);
    } catch (error) {
      console.error(error instanceof Error ? error.message : error);
      process.exitCode = 1;
    }
  });

program
  .command('extract')
  .description('Run LLM extraction on pond/ingest into pond/<namespace>.')
  .argument('<pond>', 'Path to pond directory')
  .argument('<namespace>', 'Namespace for extract output')
  .argument('<prompt>', 'Prompt to apply to each ingest item')
  .option('--model <model>', 'Override default model')
  .action(async (pond: string, namespace: string, prompt: string, options: { model?: string }) => {
    try {
      await runExtract(pond, namespace, prompt, { model: options.model });
    } catch (error) {
      console.error(error instanceof Error ? error.message : error);
      process.exitCode = 1;
    }
  });

program
  .command('store')
  .description('Chunk markdown and store in Upstash Search.')
  .argument('<pond>', 'Path to pond directory')
  .argument('[namespace]', 'Namespace for extract outputs (defaults to ingest)')
  .option('--max-chunk-size <size>', 'Maximum chunk size', (value) => Number(value), 1500)
  .action(async (pond: string, namespace: string | undefined, options: { maxChunkSize: number }) => {
    try {
      await runStore(pond, namespace, { maxChunkSize: options.maxChunkSize });
    } catch (error) {
      console.error(error instanceof Error ? error.message : error);
      process.exitCode = 1;
    }
  });

program.parseAsync(process.argv).catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
