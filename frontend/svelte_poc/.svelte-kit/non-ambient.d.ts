
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	type MatcherParam<M> = M extends (param : string) => param is (infer U extends string) ? U : string;

	export interface AppTypes {
		RouteId(): "/" | "/issues" | "/issues/[issueId]" | "/test-results" | "/[family]" | "/[family]/[artefactId]";
		RouteParams(): {
			"/issues/[issueId]": { issueId: string };
			"/[family]": { family: string };
			"/[family]/[artefactId]": { family: string; artefactId: string }
		};
		LayoutParams(): {
			"/": { issueId?: string; family?: string; artefactId?: string };
			"/issues": { issueId?: string };
			"/issues/[issueId]": { issueId: string };
			"/test-results": Record<string, never>;
			"/[family]": { family: string; artefactId?: string };
			"/[family]/[artefactId]": { family: string; artefactId: string }
		};
		Pathname(): "/" | "/issues" | `/issues/${string}` & {} | "/test-results" | `/${string}` & {} | `/${string}/${string}` & {};
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/logo.png" | string & {};
	}
}