

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.D0MFZEaQ.js","_app/immutable/chunks/C1FmrZbK.js","_app/immutable/chunks/nfCCylE5.js","_app/immutable/chunks/CSUcgsgL.js","_app/immutable/chunks/DLq7gAXq.js","_app/immutable/chunks/xDAEgHwC.js","_app/immutable/chunks/2Lvn9fxq.js","_app/immutable/chunks/6JaHWnmp.js","_app/immutable/chunks/C4CD5f_W.js","_app/immutable/chunks/4K8LNWEY.js","_app/immutable/chunks/CK189to6.js","_app/immutable/chunks/DSg9f7yw.js","_app/immutable/chunks/DSiiqZBv.js"];
export const stylesheets = ["_app/immutable/assets/0.BF_yuXM8.css"];
export const fonts = [];
