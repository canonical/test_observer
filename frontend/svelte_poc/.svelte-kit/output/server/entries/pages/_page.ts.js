import { redirect } from "@sveltejs/kit";
import { b as base } from "../../chunks/server.js";
import "../../chunks/url.js";
import "@sveltejs/kit/internal/server";
import "../../chunks/root.js";
const load = () => {
  redirect(307, `${base}/snaps`);
};
export {
  load
};
