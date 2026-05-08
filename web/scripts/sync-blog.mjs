// Sync ../BLOG_POST.md into src/pages/blog-post.md with the layout frontmatter
// pre-pended. Runs as the `prebuild` step so the route is always in sync with
// the source-of-truth markdown at the project root.
//
// Usage:
//   node scripts/sync-blog.mjs

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "..", "..", "BLOG_POST.md");
const OUT = resolve(here, "..", "src", "pages", "blog-post.md");

const body = readFileSync(SRC, "utf8");

// Pull title from the first H1 line. Pull status from the first blockquote.
const titleMatch = body.match(/^#\s+(.+)$/m);
const statusMatch = body.match(/^>\s*\*\*Status:\s*([^*]+?)\*\*\s*([^\n]*)/m);

const title = titleMatch ? titleMatch[1].trim() : "Blog post";
const status = statusMatch
  ? `Status: ${statusMatch[1].trim().replace(/\.+$/, "")}`
  : "";

const description =
  "Within the Gemma 4 Dense family, single-vector English abliteration peaks at the mid-size (4B) model, not at the largest. Cross-size compliance results across 7 languages.";

const lines = [
  "---",
  `layout: ../layouts/BlogPostLayout.astro`,
  `title: ${JSON.stringify(title)}`,
  `description: ${JSON.stringify(description)}`,
];
if (status) lines.push(`status: ${JSON.stringify(status)}`);
lines.push("---", "");
const frontmatter = lines.join("\n") + "\n";

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, frontmatter + body, "utf8");

console.log(`synced: ${SRC} -> ${OUT}`);
console.log(`  title:  ${title}`);
if (status) console.log(`  status: ${status}`);
