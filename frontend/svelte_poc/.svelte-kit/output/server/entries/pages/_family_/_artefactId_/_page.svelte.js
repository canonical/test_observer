import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import { p as page } from "../../../../chunks/index.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<h1>Artefact #${escape_html(page.params.artefactId)}</h1> <p>Coming soon.</p>`);
  });
}
export {
  _page as default
};
