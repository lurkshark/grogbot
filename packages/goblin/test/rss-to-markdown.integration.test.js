import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { mkdtemp, readFile, readdir, rm, stat } from "node:fs/promises";
import test from "node:test";
import assert from "node:assert/strict";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, "fixtures");

async function runFixture({ input, expected, outputName }) {
  const { scrapeFeed } = await import("../dist/scraper.js");
  const outputDir = await mkdtemp(path.join(fixturesDir, ".tmp-"));
  try {
    const inputPath = path.join(fixturesDir, input);
    await scrapeFeed(inputPath, { outputDir, overwrite: true });

    const writtenFiles = await readdir(outputDir);
    assert.equal(writtenFiles.length, 1);
    assert.equal(writtenFiles[0], outputName);

    const actual = await readFile(path.join(outputDir, outputName), "utf8");
    const expectedPath = path.join(fixturesDir, expected);
    const expectedContent = await readFile(expectedPath, "utf8");
    const normalizedExpected = expectedContent.replace(
      "file:///REPLACED_BY_TEST",
      pathToFileURL(fixturesDir).href,
    );
    assert.equal(actual, normalizedExpected);
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
}

async function runPaginationFixture({ input, maxPosts, expectedFiles }) {
  const { scrapeFeed } = await import("../dist/scraper.js");
  const outputDir = await mkdtemp(path.join(fixturesDir, ".tmp-"));
  try {
    const inputPath = path.join(fixturesDir, input);
    await scrapeFeed(inputPath, {
      outputDir,
      overwrite: true,
      maxPosts,
    });

    const writtenFiles = (await readdir(outputDir)).sort();
    assert.deepEqual(writtenFiles, expectedFiles.sort());
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
}

async function runCountFixture({ input, maxPosts }) {
  const { scrapeFeed } = await import("../dist/scraper.js");
  const outputDir = await mkdtemp(path.join(fixturesDir, ".tmp-"));
  try {
    const inputPath = path.join(fixturesDir, input);
    await scrapeFeed(inputPath, {
      outputDir,
      overwrite: true,
      maxPosts,
    });

    const writtenFiles = await readdir(outputDir);
    return writtenFiles.length;
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
}

test("offline RSS conversion uses repository-local fixtures", async () => {
  await runFixture({
    input: "typical-feed.xml",
    expected: "typical-expected.md",
    outputName: "2026-02-21-first-post.md",
  });
});

test("offline RSS conversion handles missing optional fields", async () => {
  await runFixture({
    input: "missing-fields.xml",
    expected: "missing-fields-expected.md",
    outputName: "2026-02-21-untitled-thoughts.md",
  });
});

test("CLI supports repository-local feed fixtures", async () => {
  const { run } = await import("../dist/command.js");
  const outputDir = await mkdtemp(path.join(fixturesDir, ".tmp-"));
  try {
    const inputPath = path.join(fixturesDir, "typical-feed.xml");
    await run(["scrape", inputPath, "--out", outputDir, "--overwrite"]);
    const targetPath = path.join(outputDir, "2026-02-21-first-post.md");
    const stats = await stat(targetPath);
    assert.equal(stats.isFile(), true);
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});

test("paginates Blogger feeds until end", async () => {
  await runPaginationFixture({
    input: "blogger-feed-page1.xml",
    expectedFiles: [
      "2026-02-21-page-one-post.md",
      "2026-02-21-page-two-post.md",
    ],
  });
});

test("paginates WordPress feeds until end", async () => {
  await runPaginationFixture({
    input: "wordpress-feed-page1.xml",
    expectedFiles: [
      "2026-02-21-wp-page-one.md",
      "2026-02-21-wp-page-two.md",
    ],
  });
});

test("stops pagination at max posts", async () => {
  await runPaginationFixture({
    input: "wordpress-feed-page1.xml",
    maxPosts: 1,
    expectedFiles: ["2026-02-21-wp-page-one.md"],
  });
});

test("defaults max posts to 100", async () => {
  const count = await runCountFixture({
    input: "wordpress-feed-page1.xml",
  });
  assert.equal(count, 2);
});

test("CLI honors max posts override", async () => {
  const { run } = await import("../dist/command.js");
  const outputDir = await mkdtemp(path.join(fixturesDir, ".tmp-"));
  try {
    const inputPath = path.join(fixturesDir, "wordpress-feed-page1.xml");
    await run([
      "scrape",
      inputPath,
      "--out",
      outputDir,
      "--overwrite",
      "--max-posts",
      "1",
    ]);
    const writtenFiles = await readdir(outputDir);
    assert.equal(writtenFiles.length, 1);
  } finally {
    await rm(outputDir, { recursive: true, force: true });
  }
});
