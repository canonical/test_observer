

export const index = 5;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/issues/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/5.bHnKBviI.js","_app/immutable/chunks/nfCCylE5.js","_app/immutable/chunks/CSUcgsgL.js","_app/immutable/chunks/DSg9f7yw.js"];
export const stylesheets = [];
export const fonts = [];
