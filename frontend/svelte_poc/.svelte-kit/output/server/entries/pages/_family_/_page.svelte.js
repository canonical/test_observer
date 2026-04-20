import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { data } = $$props;
    const displayNames = {
      snaps: "Snap Testing",
      debs: "Deb Testing",
      charms: "Charm Testing",
      images: "Image Testing"
    };
    $$renderer2.push(`<h1>${escape_html(displayNames[data.family] ?? data.family)} Dashboard</h1> <p>Coming soon.</p>`);
  });
}
export {
  _page as default
};
