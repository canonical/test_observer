

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_family_/_page.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/[family]/+page.ts";
export const imports = ["_app/immutable/nodes/3.DrcMfWWd.js","_app/immutable/chunks/C8BZa76B.js","_app/immutable/chunks/CWeFt6jb.js","_app/immutable/chunks/CJByy0VY.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/CQiZxF0l.js"];
export const stylesheets = [];
export const fonts = [];
