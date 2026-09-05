import fs from "fs";
import path from "path";

// Support being executed from either vault root or .quartz
const prefix = fs.existsSync("node_modules") ? "" : ".quartz/";

// 1. Patch files containing slugifyPath to use pure ASCII transliteration folding
const targetFiles = [
  `${prefix}node_modules/@quartz-community/crawl-links/dist/index.js`,
  `${prefix}node_modules/@quartz-community/bases-page/dist/chunk-Y4KGLVLV.js`,
  `${prefix}node_modules/@quartz-community/utils/dist/index.js`,
  `${prefix}node_modules/@quartz-community/utils/dist/path.js`,
  `${prefix}node_modules/@quartz-community/canvas-page/dist/index.js`,
  `${prefix}node_modules/@quartz-community/canvas-page/dist/components/index.js`,
  `${prefix}node_modules/@quartz-community/obsidian-flavored-markdown/dist/index.js`,
  `${prefix}node_modules/@quartz-community/note-properties/dist/index.js`,
  `${prefix}node_modules/@quartz-community/note-properties/dist/components/index.js`
];

const slugRegex = /function slugifyPath\([a-zA-Z0-9_]*\)\s*\{[\s\S]*?\n\}/g;

let patchedCount = 0;
for (const file of targetFiles) {
  if (!fs.existsSync(file)) {
    console.warn(`File not found: ${file}`);
    continue;
  }
  let text = fs.readFileSync(file, "utf8");
  if (slugRegex.test(text)) {
    text = text.replace(slugRegex, (match) => {
      const param = match.match(/function slugifyPath\(([a-zA-Z0-9_]*)\)/)[1];
      return `function slugifyPath(${param}) {
  return ${param}
    .normalize("NFD")
    .replace(/[\\u0300-\\u036f]/g, "")
    .replace(/[ʿʻʾʽ\`\\u02BF\\u02BE\\u2018\\u2019]/g, "")
    .replace(/[\\u0600-\\u06FF]/g, "")
    .split("/")
    .map(
      (segment) => segment.replace(/\\s+/g, "-").replace(/&/g, "-and-").replace(/%/g, "-percent").replace(/\\?/g, "").replace(/#/g, "").replace(/[<>:"|*]/g, "").toLowerCase()
    ).join("/").replace(/\\/$/, "");
}`;
    });
    fs.writeFileSync(file, text);
    patchedCount++;
  }
}
console.log(`Patched ${patchedCount} files with ASCII slugifyPath.`);

// 2. Patch alias-redirects
const aliasFile = `${prefix}node_modules/@quartz-community/alias-redirects/dist/index.js`;
if (fs.existsSync(aliasFile)) {
  let text = fs.readFileSync(aliasFile, "utf8");

  const oldEndsWith = `function endsWith(s2, suffix) {
  return s2 === suffix || s2.endsWith("/" + suffix);
}`;
  const newEndsWith = `function endsWith(s2, suffix) {
  if (typeof s2 !== "string") return false;
  return s2 === suffix || s2.endsWith("/" + suffix);
}`;
  text = text.replace(oldEndsWith, newEndsWith);

  const oldPathToRoot = `function pathToRoot(slug2) {
  let rootPath = slug2.split("/").filter((x2) => x2 !== "").slice(0, -1).map((_2) => "..").join("/");
  if (rootPath.length === 0) {
    rootPath = ".";
  }
  return rootPath;
}`;
  const newPathToRoot = `function pathToRoot(slug2) {
  if (!slug2 || typeof slug2 !== "string") return ".";
  let rootPath = slug2.split("/").filter((x2) => x2 !== "").slice(0, -1).map((_2) => "..").join("/");
  if (rootPath.length === 0) {
    rootPath = ".";
  }
  return rootPath;
}`;
  text = text.replace(oldPathToRoot, newPathToRoot);

  const newProcess = `function slugifyAlias(s) {
  if (!s || typeof s !== "string") return "";
  const cleaned = s
    .normalize("NFD")
    .replace(/[\\u0300-\\u036f]/g, "")
    .replace(/[ʿʻʾʽ\`\\u02BF\\u02BE\\u2018\\u2019]/g, "")
    .replace(/[\\u0600-\\u06FF]/g, "")
    .split("/")
    .map(
      (segment) => segment.replace(/\\s+/g, "-").replace(/&/g, "-and-").replace(/%/g, "-percent").replace(/\\?/g, "").replace(/#/g, "").replace(/[<>:"|*]/g, "").toLowerCase()
    ).join("/").replace(/\\/$/, "");
  return cleaned;
}

function* processAliases(ctx, file, emittedPaths) {
  if (!file?.data?.slug) return;
  const ogSlug = simplifySlug(String(file.data.slug));
  for (const rawAlias of file.data.aliases ?? []) {
    if (!rawAlias || typeof rawAlias !== "string") continue;
    const aliasTarget = slugifyAlias(rawAlias);
    if (!aliasTarget || aliasTarget === ogSlug) continue;
    const aliasTargetSlug = isRelativeURL(aliasTarget) ? path.normalize(path.join(ogSlug, "..", aliasTarget)) : aliasTarget;
    if (!aliasTargetSlug || typeof aliasTargetSlug !== "string" || emittedPaths.has(aliasTargetSlug)) continue;
    emittedPaths.add(aliasTargetSlug);
    const redirUrl = resolveRelative(aliasTargetSlug, ogSlug);
    yield write(ctx, aliasTargetSlug, ".html", redirectHtml(ogSlug, redirUrl));
  }
}`;
  text = text.replace(/function\* processAliases\(ctx, file, emittedPaths\) \{[\s\S]*?\n\}/, newProcess);
  fs.writeFileSync(aliasFile, text);
  console.log("Patched alias-redirects successfully.");
} else {
  console.warn(`AliasRedirects file not found: ${aliasFile}`);
}

console.log("Quartz node_modules patched successfully for clean ASCII slugs!");
