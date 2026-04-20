

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+page.ts";
export const imports = ["_app/immutable/nodes/2.1PMv4O-h.js","_app/immutable/chunks/C8BZa76B.js","_app/immutable/chunks/CWeFt6jb.js","_app/immutable/chunks/tG4pQtLZ.js","_app/immutable/chunks/C0-tmwDq.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/CJByy0VY.js","_app/immutable/chunks/2vXu73ch.js"];
export const stylesheets = [];
export const fonts = [];
