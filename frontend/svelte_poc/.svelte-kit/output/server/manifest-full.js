export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "svelte_poc/_app",
	assets: new Set(["logo.png"]),
	mimeTypes: {".png":"image/png"},
	_: {
		client: {start:"_app/immutable/entry/start.Bci6sCH3.js",app:"_app/immutable/entry/app.Bhmr9b_H.js",imports:["_app/immutable/entry/start.Bci6sCH3.js","_app/immutable/chunks/DFu1i5F5.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/tG4pQtLZ.js","_app/immutable/chunks/C0-tmwDq.js","_app/immutable/chunks/CWeFt6jb.js","_app/immutable/entry/app.Bhmr9b_H.js","_app/immutable/chunks/CTOPHCKn.js","_app/immutable/chunks/CQiZxF0l.js","_app/immutable/chunks/CJByy0VY.js","_app/immutable/chunks/C0-tmwDq.js","_app/immutable/chunks/CY2gN3rf.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js')),
			__memo(() => import('./nodes/4.js')),
			__memo(() => import('./nodes/5.js')),
			__memo(() => import('./nodes/6.js')),
			__memo(() => import('./nodes/7.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/issues",
				pattern: /^\/issues\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/issues/[issueId]",
				pattern: /^\/issues\/([^/]+?)\/?$/,
				params: [{"name":"issueId","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/test-results",
				pattern: /^\/test-results\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/[family]",
				pattern: /^\/([^/]+?)\/?$/,
				params: [{"name":"family","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			},
			{
				id: "/[family]/[artefactId]",
				pattern: /^\/([^/]+?)\/([^/]+?)\/?$/,
				params: [{"name":"family","optional":false,"rest":false,"chained":false},{"name":"artefactId","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
