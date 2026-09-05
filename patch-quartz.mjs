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


// 3. Ensure Noto Naskh Arabic is fetched alongside Noto Serif
const themeFile = `${prefix}quartz/util/theme.ts`;
if (fs.existsSync(themeFile)) {
  let text = fs.readFileSync(themeFile, "utf8");
  if (!text.includes("Noto+Naskh+Arabic")) {
    text = text.replace(
      "return `https://fonts.googleapis.com/css2?family=${headerFont}&family=${bodyFont}&family=${codeFont}&display=swap`",
      "return `https://fonts.googleapis.com/css2?family=${headerFont}&family=${bodyFont}&family=${codeFont}&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap`"
    );
    fs.writeFileSync(themeFile, text);
    console.log("Patched googleFontHref in theme.ts to include Noto Naskh Arabic.");
  }
}


// 4. Enhance interactive graph view: hitArea for immediate hover, clear crisp labels with stroke, smooth physics
const graphFile = `${prefix}node_modules/@quartz-community/graph/dist/index.js`;
if (fs.existsSync(graphFile)) {
  let text = fs.readFileSync(graphFile, "utf8");

  // A. Expand hitArea to generous radius so hovering is immediate, accurate, and responsive
  const oldCircle = "var U=new o.Graphics;U.circle(0,0,Tu),U.fill({color:De?He:le}),De&&U.stroke({width:2,color:ue}),U.eventMode=\"static\",U.cursor=\"pointer\",U.label=ie,";
  const newCircle = "var U=new o.Graphics;U.circle(0,0,Tu),U.fill({color:De?He:le}),De&&U.stroke({width:2,color:ue}),U.hitArea=new o.Circle(0,0,Math.max(Tu+8,14)),U.eventMode=\"static\",U.cursor=\"pointer\",U.label=ie,";
  if (text.includes(oldCircle)) {
    text = text.replace(oldCircle, newCircle);
  }

  // B. Clean, legible text styling with contrast outline and proper padding
  const oldText = "style:{fontSize:We*15,fill:ze,fontFamily:Ne},resolution:window.devicePixelRatio*4";
  const newText = "style:{fontSize:Math.max(We*16,11),fill:ze,fontFamily:Ne,stroke:{color:He,width:3},padding:4},resolution:window.devicePixelRatio*4";
  if (text.includes(oldText)) {
    text = text.replace(oldText, newText);
  }

  // C. Immediate hover trigger with pointerenter
  const oldPointer = "A.on(\"pointerover\",function(N){Wu(F.id),j=v.alpha,Eu||Au()}),A.on(\"pointerleave\",function(){Wu(null),v.alpha=j,Eu||Au()})";
  const newPointer = "A.on(\"pointerenter\",function(N){Wu(F.id),Au()}),A.on(\"pointerleave\",function(){Wu(null),Au()})";
  if (text.includes(oldPointer)) {
    text = text.replace(oldPointer, newPointer);
  }

  // D. Smooth label scaling on hover and bring active label to top
  const oldQe = "function qe(){for(var i=1/qu,l=i*1.1,F=0;F<L.length;F++){var A=L[F];_u===A.simulationData.id?(A.label.alpha=1,A.label.scale.set(l)):A.label.scale.set(i)}}";
  const newQe = "function qe(){for(var i=1/qu,l=i*1.15,F=0;F<L.length;F++){var A=L[F];if(_u===A.simulationData.id){A.label.alpha=1;A.label.scale.set(l);vu.addChild(A.label)}else{A.label.scale.set(i);A.label.alpha=P.k>1.4?1:0}}}";
  if (text.includes(oldQe)) {
    text = text.replace(oldQe, newQe);
  }

  // E. Smooth physics damping (velocityDecay 0.3 for gentle, stable settling)
  const oldSim = "var au=a.forceSimulation(nu)";
  const newSim = "var au=a.forceSimulation(nu).velocityDecay(0.35)";
  if (text.includes(oldSim) && !text.includes(newSim)) {
    text = text.replace(oldSim, newSim);
  }

  fs.writeFileSync(graphFile, text);
  console.log("Patched graph component for smooth physics and responsive hovering.");
}

console.log("Quartz node_modules patched successfully for clean ASCII slugs!");
