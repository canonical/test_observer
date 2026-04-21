import { error } from "@sveltejs/kit";
import { c as FAMILIES, d as FAMILY_TO_API } from "../../../chunks/index2.js";
import { API_BASE } from "../../../chunks/config.js";
const load = async ({ params, fetch }) => {
  const family = params.family;
  if (!FAMILIES.includes(family)) {
    error(404, `Unknown family: ${family}`);
  }
  const apiFamily = FAMILY_TO_API[family];
  const res = await fetch(`${API_BASE}/v1/artefacts?family=${apiFamily}`, {
    credentials: "include",
    headers: { "X-CSRF-Token": "1" }
  });
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      const returnTo = typeof window !== "undefined" ? window.location.href : "";
      const loginUrl = `${API_BASE}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      if (typeof window !== "undefined") {
        window.location.href = loginUrl;
      }
      return { family, artefacts: [] };
    }
    error(res.status, "Failed to load artefacts");
  }
  const artefacts = await res.json();
  return {
    family,
    artefacts
  };
};
export {
  load
};
