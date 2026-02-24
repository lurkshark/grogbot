#!/usr/bin/env node
import { Command } from 'commander';
import { runExtract } from './commands/extract.js';
import { runTransform } from './commands/transform.js';
import { runLoad } from './commands/load.js';

const program = new Command();

program
  .name('goblin')
  .description('RSS extract, LLM transform, and load pipeline for Grogbot.')
  .showHelpAfterError();

program
  .command('extract')
  .description('Extract an RSS feed into pond/ingest.')
  .argument('<pond>', 'Path to pond directory')
  .argument('<feedUrl>', 'RSS feed URL')
  .action(async (pond: string, feedUrl: string) => {
    try {
      await runExtract(pond, feedUrl);
    } catch (error) {
      console.error(error instanceof Error ? error.message : error);
      process.exitCode = 1;
    }
  });

program
  .command('transform')
  .description('Run LLM transform on pond/ingest into pond/<namespace>.')
  .argument('<pond>', 'Path to pond directory')
  .argument('<namespace>', 'Namespace for transform output')
  .argument('<prompt>', 'Prompt to apply to each extracted item')
  .option('--model <model>', 'Override default model')
  .action(async (pond: string, namespace: string, prompt: string, options: { model?: string }) => {
    try {
      await runTransform(pond, namespace, prompt, { model: options.model });
    } catch (error) {
      console.error(error instanceof Error ? error.message : error);
      process.exitCode = 1;
    }
  });

program
  .command('load')
  .description('Chunk markdown and load into Upstash Search.')
  .argument('<pond>', 'Path to pond directory')
  .argument('[namespace]', 'Namespace for transform outputs (defaults to RSS extract output)')
  .option('--max-chunk-size <size>', 'Maximum chunk size', (value) => Number(value), 1500)
  .action(
    async (pond: string, namespace: string | undefined, options: { maxChunkSize: number }) => {
      try {
        await runLoad(pond, namespace, { maxChunkSize: options.maxChunkSize });
      } catch (error) {
        console.error(error instanceof Error ? error.message : error);
        process.exitCode = 1;
      }
    },
  );

program.parseAsync(process.argv).catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
