import "clsx";
import { a as attr, b as attr_class, e as escape_html, c as ensure_array_like, d as derived, s as stringify } from "../../chunks/root.js";
import { p as page } from "../../chunks/index.js";
import { b as base } from "../../chunks/server.js";
import "../../chunks/url.js";
import "@sveltejs/kit/internal/server";
import { configuredTabs, helpLinks } from "../../chunks/config.js";
function NavbarEntry($$renderer, $$props) {
  let { href, title, isActive } = $$props;
  let isHovered = false;
  $$renderer.push(`<a${attr("href", href)}${attr_class("nav-entry svelte-ockbil", void 0, { "active": isActive, "hovered": isHovered })}>${escape_html(title)}</a>`);
}
function NavbarDropdown($$renderer, $$props) {
  let { label, children } = $$props;
  let isOpen = false;
  $$renderer.push(`<div class="nav-dropdown svelte-1uas4bk"><button class="dropdown-trigger svelte-1uas4bk"${attr("aria-expanded", isOpen)}>${escape_html(label)} ▾</button> `);
  {
    $$renderer.push("<!--[-1-->");
  }
  $$renderer.push(`<!--]--></div>`);
}
class UserStore {
  current = null;
  get isLoggedIn() {
    return this.current !== null;
  }
  get initials() {
    if (!this.current) return "";
    const parts = this.current.name.split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return (parts[0]?.[0] ?? "").toUpperCase();
  }
  set(user) {
    this.current = user;
  }
}
const userStore = new UserStore();
function Navbar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const pathname = derived(() => page.url.pathname);
    function loginUrl() {
      return `/v1/auth/saml/login?return_to=${encodeURIComponent(window.location.href)}`;
    }
    function logoutUrl() {
      return `/v1/auth/saml/logout?return_to=${encodeURIComponent(window.location.href)}`;
    }
    $$renderer2.push(`<nav class="navbar svelte-rfuq4y" aria-label="Main navigation"><div class="navbar-inner svelte-rfuq4y"><a${attr("href", `${stringify(base)}/`)} class="logo svelte-rfuq4y"><img${attr("src", `${stringify(base)}/logo.png`)} alt="Test Observer" height="28" class="svelte-rfuq4y" onerror="this.__e=event"/></a> <!--[-->`);
    const each_array = ensure_array_like(configuredTabs);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      NavbarEntry($$renderer2, {
        href: tab.href,
        title: tab.label,
        isActive: pathname().startsWith(tab.href)
      });
    }
    $$renderer2.push(`<!--]--> <div class="spacer svelte-rfuq4y"></div> `);
    NavbarEntry($$renderer2, {
      href: `${stringify(base)}/test-results`,
      title: "Search",
      isActive: pathname().startsWith(`${base}/test-results`)
    });
    $$renderer2.push(`<!----> `);
    NavbarEntry($$renderer2, {
      href: `${stringify(base)}/issues`,
      title: "Issues",
      isActive: pathname().startsWith(`${base}/issues`)
    });
    $$renderer2.push(`<!----> `);
    NavbarDropdown($$renderer2, {
      label: "Help",
      children: ($$renderer3) => {
        $$renderer3.push(`<!--[-->`);
        const each_array_1 = ensure_array_like(helpLinks);
        for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
          let link = each_array_1[$$index_1];
          $$renderer3.push(`<a${attr("href", link.href)} target="_blank" rel="noopener noreferrer">${escape_html(link.label)}</a>`);
        }
        $$renderer3.push(`<!--]-->`);
      }
    });
    $$renderer2.push(`<!----> `);
    if (userStore.isLoggedIn) {
      $$renderer2.push("<!--[0-->");
      NavbarDropdown($$renderer2, {
        label: userStore.current?.name ?? "",
        children: ($$renderer3) => {
          $$renderer3.push(`<a${attr("href", logoutUrl())}>Log out</a>`);
        }
      });
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<a${attr("href", loginUrl())} class="nav-button svelte-rfuq4y">Log in</a>`);
    }
    $$renderer2.push(`<!--]--></div></nav>`);
  });
}
class ErrorStore {
  message = null;
  get hasError() {
    return this.message !== null;
  }
  set(msg) {
    this.message = msg;
  }
  clear() {
    this.message = null;
  }
}
const errorStore = new ErrorStore();
function ErrorPopup($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    if (errorStore.hasError) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="overlay svelte-1qcd3ro" role="presentation"><dialog class="error-dialog svelte-1qcd3ro" open="" aria-modal="true" role="alertdialog"><h2 class="svelte-1qcd3ro">Error</h2> <p>${escape_html(errorStore.message)}</p> <button type="button" class="svelte-1qcd3ro">Dismiss</button></dialog></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { data, children } = $$props;
    $$renderer2.push(`<div class="app-shell svelte-12qhfyh">`);
    Navbar($$renderer2);
    $$renderer2.push(`<!----> <main class="main-content svelte-12qhfyh">`);
    children($$renderer2);
    $$renderer2.push(`<!----></main> `);
    ErrorPopup($$renderer2);
    $$renderer2.push(`<!----></div>`);
  });
}
export {
  _layout as default
};
