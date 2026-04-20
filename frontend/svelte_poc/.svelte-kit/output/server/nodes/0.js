

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.TH4k_Efv.js","_app/immutable/chunks/CJByy0VY.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/CY2gN3rf.js","_app/immutable/chunks/CQiZxF0l.js","_app/immutable/chunks/DbpBPJFn.js","_app/immutable/chunks/tG4pQtLZ.js","_app/immutable/chunks/C0-tmwDq.js","_app/immutable/chunks/CWeFt6jb.js","_app/immutable/chunks/DFu1i5F5.js","_app/immutable/chunks/2vXu73ch.js","_app/immutable/chunks/BNN4KTX5.js"];
export const stylesheets = ["_app/immutable/assets/0.C5DGKVC7.css"];
export const fonts = [];
