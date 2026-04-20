

export const index = 5;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/issues/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/5.C6DZ5L0F.js","_app/immutable/chunks/CJByy0VY.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/2vXu73ch.js"];
export const stylesheets = [];
export const fonts = [];
