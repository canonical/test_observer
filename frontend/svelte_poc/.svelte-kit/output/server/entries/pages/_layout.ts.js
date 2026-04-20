const ssr = false;
const prerender = false;
const load = async ({ fetch }) => {
  try {
    const res = await fetch("/v1/users/me", {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" }
    });
    if (res.ok) {
      const user = await res.json();
      return { user };
    }
  } catch {
  }
  return { user: null };
};
export {
  load,
  prerender,
  ssr
};
