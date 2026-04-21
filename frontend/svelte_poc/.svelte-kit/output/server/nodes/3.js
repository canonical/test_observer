

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_family_/_page.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/[family]/+page.ts";
export const imports = ["_app/immutable/nodes/3.PfUnrZBo.js","_app/immutable/chunks/B4y3sYDL.js","_app/immutable/chunks/6JaHWnmp.js","_app/immutable/chunks/C4CD5f_W.js","_app/immutable/chunks/CSUcgsgL.js","_app/immutable/chunks/2Lvn9fxq.js","_app/immutable/chunks/nfCCylE5.js","_app/immutable/chunks/xDAEgHwC.js","_app/immutable/chunks/DLq7gAXq.js","_app/immutable/chunks/4K8LNWEY.js","_app/immutable/chunks/CK189to6.js"];
export const stylesheets = ["_app/immutable/assets/3.PSkc4BCS.css"];
export const fonts = [];
