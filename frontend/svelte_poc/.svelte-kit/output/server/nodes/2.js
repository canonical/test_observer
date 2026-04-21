

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+page.ts";
export const imports = ["_app/immutable/nodes/2.BRSDLWXL.js","_app/immutable/chunks/B4y3sYDL.js","_app/immutable/chunks/6JaHWnmp.js","_app/immutable/chunks/C4CD5f_W.js","_app/immutable/chunks/CSUcgsgL.js","_app/immutable/chunks/nfCCylE5.js","_app/immutable/chunks/DSg9f7yw.js"];
export const stylesheets = [];
export const fonts = [];
