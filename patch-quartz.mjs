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
  if (!text.includes("function slugifyAlias")) {
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
  }
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


// 4. Match Obsidian dynamic graph behavior (interactive hover-revealed labels, direct pointerover, crisp text)
const graphFiles = [
  `${prefix}node_modules/@quartz-community/graph/dist/index.js`,
  `${prefix}node_modules/@quartz-community/graph/dist/components/index.js`
];

for (const graphFile of graphFiles) {
  if (!fs.existsSync(graphFile)) continue;
  let text = fs.readFileSync(graphFile, "utf8");

  // A. Generous hitArea on bubbles so hover is immediate and accurate
  const oldCircle = "var U=new o.Graphics;U.circle(0,0,Tu),U.fill({color:De?He:le}),De&&U.stroke({width:2,color:ue}),U.eventMode=\"static\",U.cursor=\"pointer\",U.label=ie,";
  const newCircle = "var U=new o.Graphics;U.circle(0,0,Tu),U.fill({color:De?He:le}),De&&U.stroke({width:2,color:ue}),U.hitArea=new o.Circle(0,0,Math.max(Tu+10,16)),U.eventMode=\"static\",U.cursor=\"pointer\",U.label=ie,";
  if (text.includes(oldCircle)) {
    text = text.replace(oldCircle, newCircle);
  }

  // B. Obsidian typography: clean font with contrast outline stroke, crisp resolution
  const oldText = "style:{fontSize:We*15,fill:ze,fontFamily:Ne},resolution:window.devicePixelRatio*4";
  const newText = "style:{fontSize:Math.max(We*16,12),fill:ze,fontFamily:Ne,stroke:{color:He,width:3},padding:4},resolution:window.devicePixelRatio*4";
  if (text.includes(oldText)) {
    text = text.replace(oldText, newText);
  }

  // C. Immediate hover trigger with pointerenter
  const oldPointer = "A.on(\"pointerover\",function(N){Wu(F.id),j=v.alpha,Eu||Au()}),A.on(\"pointerleave\",function(){Wu(null),v.alpha=j,Eu||Au()})";
  const newPointer = "A.on(\"pointerenter\",function(N){Wu(F.id),Au()}),A.on(\"pointerleave\",function(){Wu(null),Au()})";
  if (text.includes(oldPointer)) {
    text = text.replace(oldPointer, newPointer);
  }

  // D. Dynamic label visibility matching Obsidian:
  //    - Idle: labels are 100% hidden (clean, uncluttered graph)
  //    - Hovered node: label is 100% visible, scaled up, and elevated to top
  //    - Neighbor nodes: labels become visible (0.9 alpha) so you see connections!
  const oldQe = "function qe(){for(var i=1/qu,l=i*1.1,F=0;F<L.length;F++){var A=L[F];_u===A.simulationData.id?(A.label.alpha=1,A.label.scale.set(l)):A.label.scale.set(i)}}";
  const newQe = "function qe(){for(var i=1/qu,l=i*1.2,F=0;F<L.length;F++){var A=L[F];if(_u===A.simulationData.id){A.label.alpha=1;A.label.scale.set(l);vu.addChild(A.label)}else if(_u!==null&&A.active){A.label.alpha=0.9;A.label.scale.set(i);vu.addChild(A.label)}else{A.label.scale.set(i);A.label.alpha=0}}}";
  if (text.includes(oldQe)) {
    text = text.replace(oldQe, newQe);
  }

  // E. Zoom label updates: maintain dynamic hover visibility while zooming
  const oldUt = "for(var v=0;v<vu.children.length;v++){var j=vu.children[v];A.indexOf(j)===-1&&(j.alpha=F)}";
  const newUt = "for(var v=0;v<vu.children.length;v++){var j=vu.children[v];if(A.indexOf(j)===-1){j.alpha=0}}";
  if (text.includes(oldUt)) {
    text = text.replace(oldUt, newUt);
  }

  // F. Smooth elastic physics (damping 0.35)
  const oldSim = "var au=a.forceSimulation(nu)";
  const newSim = "var au=a.forceSimulation(nu).velocityDecay(0.35)";
  if (text.includes(oldSim) && !text.includes(newSim)) {
    text = text.replace(oldSim, newSim);
  }

  // G. Homepage "/" and "index" resolution to "the-sirah"
  const oldM = "var m=Fu(w);m===\"\"&&(m=\"index\");";
  const newM = "var m=Fu(w);(m===\"\"||m===\"/\")&&(m=\"the-sirah\");m===\"index\"&&(m=\"the-sirah\");";
  if (text.includes(oldM)) {
    text = text.replace(oldM, newM);
  }

  // H. Generous drag hit tolerance (20px instead of 5px)
  const oldJe = "var Je=function(i){for(var l=(i.x-P.x)/P.k,F=(i.y-P.y)/P.k,A=0;A<nu.length;A++){var v=nu[A],j=l-v.x-R/2,N=F-v.y-O/2,K=Math.sqrt(j*j+N*N),gu=ae(v);if(K<gu+5)return v}return null}";
  const newJe = "var Je=function(i){for(var l=(i.x-P.x)/P.k,F=(i.y-P.y)/P.k,A=0;A<nu.length;A++){var v=nu[A],j=l-v.x-R/2,N=F-v.y-O/2,K=Math.sqrt(j*j+N*N),gu=Math.max(ae(v)+12,20);if(K<gu)return v}return null}";
  if (text.includes(oldJe)) {
    text = text.replace(oldJe, newJe);
  }

  // I. Full canvas-level pointermove hit detection (guarantees 100% of dots respond on hover without pixel-hunting)
  const oldDrag = "Qe=a.drag().container(Z.canvas).subject(Je).on(\"start\",Xe).on(\"drag\",Ye).on(\"end\",Ze);a.select(Z.canvas).call(Qe)";
  const newDrag = "Qe=a.drag().container(Z.canvas).subject(Je).on(\"start\",Xe).on(\"drag\",Ye).on(\"end\",Ze);a.select(Z.canvas).call(Qe);Z.canvas.addEventListener(\"pointermove\",function(ev){var rect=Z.canvas.getBoundingClientRect();var sx=ev.clientX-rect.left,sy=ev.clientY-rect.top;var wx=(sx-P.x)/P.k-R/2,wy=(sy-P.y)/P.k-O/2;var hit=null,minDist=Infinity;for(var ai=0;ai<nu.length;ai++){var node=nu[ai];var dx=wx-node.x,dy=wy-node.y;var dist=Math.sqrt(dx*dx+dy*dy);var rHit=Math.max(ae(node)+10,18);if(dist<rHit&&dist<minDist){minDist=dist;hit=node;}}if(hit){if(_u!==hit.id){Wu(hit.id);Au();Z.canvas.style.cursor=\"pointer\";}}else{if(_u!==null&&!Eu){Wu(null);Au();Z.canvas.style.cursor=\"default\";}}});Z.canvas.addEventListener(\"pointerleave\",function(){if(!Eu&&_u!==null){Wu(null);Au();Z.canvas.style.cursor=\"default\";}});";
  if (text.includes(oldDrag) && !text.includes("Z.canvas.addEventListener(\"pointermove\"")) {
    text = text.replace(oldDrag, newDrag);
  }

  fs.writeFileSync(graphFile, text);
  console.log(`Patched graph component in ${graphFile} for dynamic Obsidian-style labels, 100% reliable canvas hover, and smooth physics.`);
}

console.log("Quartz node_modules patched successfully for clean ASCII slugs!");
