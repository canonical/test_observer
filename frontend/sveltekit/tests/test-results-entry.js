import { flushSync, mount, unmount } from "svelte";
import Page from "../src/routes/test-results/+page.svelte";
import {
  requests,
  resetApi,
  setHandler,
} from "$lib/api/client";

/** @param {import("svelte").MountOptions["target"]} target */
export function mountPage(target) {
  const component = mount(Page, { target });
  flushSync();
  return component;
}

export { flushSync, requests, resetApi, setHandler, unmount as unmountPage };
