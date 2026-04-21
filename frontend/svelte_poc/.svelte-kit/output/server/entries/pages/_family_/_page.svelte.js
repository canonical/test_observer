import { e as escape_html, b as attr_class, d as derived, f as attr_style, s as stringify, a as attr, c as ensure_array_like } from "../../../chunks/root.js";
import { p as page } from "../../../chunks/index.js";
import { F as FAMILY_TITLES, S as STATUS_COLORS, a as STATUS_LABELS, f as formatDueDate, u as userInitials, s as stageDisplayName, b as FAMILY_STAGES } from "../../../chunks/index2.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/url.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/exports.js";
import { b as base } from "../../../chunks/server.js";
const FAMILY_FILTERS = {
  snaps: [
    { key: "Assignee", extract: (a) => a.assignee?.name ?? "Unassigned" },
    { key: "Status", extract: (a) => a.status },
    { key: "Due date", extract: (a) => dueDateCategory(a.due_date) },
    { key: "Risk", extract: (a) => a.stage }
  ],
  debs: [
    { key: "Assignee", extract: (a) => a.assignee?.name ?? "Unassigned" },
    { key: "Status", extract: (a) => a.status },
    { key: "Due date", extract: (a) => dueDateCategory(a.due_date) },
    { key: "Series", extract: (a) => a.series },
    { key: "Pocket", extract: (a) => a.stage }
  ],
  charms: [
    { key: "Assignee", extract: (a) => a.assignee?.name ?? "Unassigned" },
    { key: "Status", extract: (a) => a.status },
    { key: "Due date", extract: (a) => dueDateCategory(a.due_date) },
    { key: "Risk", extract: (a) => a.stage }
  ],
  images: [
    { key: "OS type", extract: (a) => a.os },
    { key: "Release", extract: (a) => a.release },
    { key: "Owner", extract: (a) => a.owner },
    { key: "Assignee", extract: (a) => a.assignee?.name ?? "Unassigned" },
    { key: "Status", extract: (a) => a.status },
    { key: "Due date", extract: (a) => dueDateCategory(a.due_date) }
  ]
};
function dueDateCategory(dueDate) {
  if (!dueDate) return "No due date";
  const due = new Date(dueDate);
  const now = /* @__PURE__ */ new Date();
  if (due < now) return "Overdue";
  const diffDays = (due.getTime() - now.getTime()) / (1e3 * 60 * 60 * 24);
  if (diffDays < 7) return "Within a week";
  return "More than a week";
}
class ViewModeStore {
  mode = this.load();
  load() {
    return "dashboard";
  }
  set(value) {
    this.mode = value;
  }
}
const viewModeStore = new ViewModeStore();
function DashboardHeader($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { family, filteredCount, totalCount } = $$props;
    const title = derived(() => FAMILY_TITLES[family]);
    const countText = derived(() => filteredCount === totalCount ? `${totalCount} artifacts` : `${filteredCount} of ${totalCount} artifacts`);
    $$renderer2.push(`<header class="dashboard-header svelte-tyda9u"><div class="title-group svelte-tyda9u"><h1 class="title svelte-tyda9u">${escape_html(title())}</h1> <span class="count svelte-tyda9u">${escape_html(countText())}</span></div> <div class="view-toggle svelte-tyda9u"><button${attr_class("toggle-btn svelte-tyda9u", void 0, { "active": viewModeStore.mode === "list" })} title="List view"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"></path></svg></button> <button${attr_class("toggle-btn svelte-tyda9u", void 0, { "active": viewModeStore.mode === "dashboard" })} title="Dashboard view"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h8v8H3V3zm0 10h8v8H3v-8zm10-10h8v8h-8V3zm0 10h8v8h-8v-8z"></path></svg></button></div></header>`);
  });
}
function FilterSidebar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { family } = $$props;
    const filterDefs = derived(() => FAMILY_FILTERS[family]);
    page.url.searchParams.get("q") ?? "";
    Object.fromEntries(filterDefs().map((d) => [d.key, true]));
    {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function StatusChip($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { status } = $$props;
    $$renderer2.push(`<span class="status-chip svelte-m1p3zv"${attr_style(`color: ${stringify(STATUS_COLORS[status])}; border-color: ${stringify(STATUS_COLORS[status])};`)}>${escape_html(STATUS_LABELS[status])}</span>`);
  });
}
function DueDateChip($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { dueDate } = $$props;
    const formatted = derived(() => formatDueDate(dueDate));
    if (formatted()) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="due-chip svelte-oww5bz">Due ${escape_html(formatted())}</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function UserAvatar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { assignee, completed, total } = $$props;
    const initials = derived(() => assignee ? userInitials(assignee.name) : "");
    const progress = derived(() => total > 0 ? completed / total : 0);
    const circumference = 2 * Math.PI * 18;
    const dashOffset = derived(() => circumference * (1 - progress()));
    const COLORS = [
      "#FF5252",
      "#FFFF00",
      "#448AFF",
      "#FFAB40",
      "#69F0AE",
      "#E040FB"
    ];
    const avatarColor = derived(() => assignee ? COLORS[Math.abs(assignee.id) % COLORS.length] : COLORS[5]);
    function darkenColor(hex) {
      const r = parseInt(hex.slice(1, 3), 16) / 255;
      const g = parseInt(hex.slice(3, 5), 16) / 255;
      const b = parseInt(hex.slice(5, 7), 16) / 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b);
      let h = 0, s = 0, l = (max + min) / 2;
      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        else if (max === g) h = ((b - r) / d + 2) / 6;
        else h = ((r - g) / d + 4) / 6;
      }
      l = Math.max(0, l - 0.2);
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1 / 6) return p + (q - p) * 6 * t;
        if (t < 1 / 2) return q;
        if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
        return p;
      };
      const q2 = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p2 = 2 * l - q2;
      const toHex = (v) => Math.round(v * 255).toString(16).padStart(2, "0");
      return `#${toHex(hue2rgb(p2, q2, h + 1 / 3))}${toHex(hue2rgb(p2, q2, h))}${toHex(hue2rgb(p2, q2, h - 1 / 3))}`;
    }
    const progressColor = derived(() => darkenColor(avatarColor()));
    $$renderer2.push(`<div class="avatar-wrapper svelte-tidg8l"${attr("title", `${stringify(assignee?.name ?? "Unassigned")} (${stringify(completed)}/${stringify(total)} reviews)`)}><svg width="44" height="44" viewBox="0 0 44 44" class="svelte-tidg8l"><circle cx="22" cy="22" r="18" fill="none"${attr("stroke", avatarColor())} stroke-width="2.5"></circle><circle cx="22" cy="22" r="18" fill="none"${attr("stroke", progressColor())} stroke-width="2.5"${attr("stroke-dasharray", circumference)}${attr("stroke-dashoffset", dashOffset())} stroke-linecap="round" transform="rotate(-90 22 22)"></circle></svg> `);
    if (assignee) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="initials svelte-tidg8l"${attr_style(`background-color: ${stringify(avatarColor())};`)}>${escape_html(initials())}</div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function ArtefactCard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { artefact, family } = $$props;
    const fields = derived(() => [
      artefact.track && `track: ${artefact.track}`,
      artefact.store && `store: ${artefact.store}`,
      artefact.branch && `branch: ${artefact.branch}`,
      artefact.series && `series: ${artefact.series}`,
      artefact.repo && `repo: ${artefact.repo}`,
      artefact.source && `source: ${artefact.source}`,
      artefact.os && `os: ${artefact.os}`,
      artefact.release && `release: ${artefact.release}`,
      artefact.owner && `owner: ${artefact.owner}`
    ].filter(Boolean));
    $$renderer2.push(`<a${attr("href", `${stringify(base)}/${stringify(family)}/${stringify(artefact.id)}`)} class="card svelte-1bg5ixr"><div class="card-body svelte-1bg5ixr"><h3 class="name svelte-1bg5ixr">${escape_html(artefact.name)}</h3> <p class="field svelte-1bg5ixr">version: ${escape_html(artefact.version)}</p> <!--[-->`);
    const each_array = ensure_array_like(fields());
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let field = each_array[$$index];
      $$renderer2.push(`<p class="field svelte-1bg5ixr">${escape_html(field)}</p>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="card-footer svelte-1bg5ixr">`);
    StatusChip($$renderer2, { status: artefact.status });
    $$renderer2.push(`<!----> `);
    DueDateChip($$renderer2, { dueDate: artefact.due_date });
    $$renderer2.push(`<!----> <div class="spacer svelte-1bg5ixr"></div> `);
    UserAvatar($$renderer2, {
      assignee: artefact.assignee,
      completed: artefact.completed_environment_reviews_count,
      total: artefact.all_environment_reviews_count
    });
    $$renderer2.push(`<!----></div></a>`);
  });
}
function StageColumn($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { stage, artefacts, family } = $$props;
    $$renderer2.push(`<section class="stage-column svelte-1dtea5b"><h2 class="stage-title svelte-1dtea5b">${escape_html(stageDisplayName(stage))}</h2> <div class="card-list svelte-1dtea5b"><!--[-->`);
    const each_array = ensure_array_like(artefacts);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let artefact = each_array[$$index];
      ArtefactCard($$renderer2, { artefact, family });
    }
    $$renderer2.push(`<!--]--></div></section>`);
  });
}
function ArtefactTable($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { artefacts, family } = $$props;
    const COLUMNS = {
      snaps: [
        { label: "Name", key: "name", flex: 2, getValue: (a) => a.name },
        {
          label: "Version",
          key: "version",
          flex: 2,
          getValue: (a) => a.version
        },
        {
          label: "Track",
          key: "track",
          flex: 1,
          getValue: (a) => a.track
        },
        {
          label: "Risk",
          key: "risk",
          flex: 1,
          getValue: (a) => a.stage
        },
        {
          label: "Branch",
          key: "branch",
          flex: 1,
          getValue: (a) => a.branch
        },
        {
          label: "Due date",
          key: "dueDate",
          flex: 1,
          getValue: (a) => a.due_date ? new Date(a.due_date).toLocaleDateString() : ""
        },
        {
          label: "Reviews",
          key: "reviewsRemaining",
          flex: 1,
          getValue: (a) => String(a.all_environment_reviews_count - a.completed_environment_reviews_count)
        },
        {
          label: "Status",
          key: "status",
          flex: 1,
          getValue: (a) => STATUS_LABELS[a.status],
          color: (a) => STATUS_COLORS[a.status]
        },
        {
          label: "Assignee",
          key: "assignee",
          flex: 1,
          getValue: (a) => a.assignee?.name ?? ""
        }
      ],
      debs: [
        { label: "Name", key: "name", flex: 2, getValue: (a) => a.name },
        {
          label: "Version",
          key: "version",
          flex: 2,
          getValue: (a) => a.version
        },
        {
          label: "Series",
          key: "series",
          flex: 1,
          getValue: (a) => a.series
        },
        { label: "Repo", key: "repo", flex: 1, getValue: (a) => a.repo },
        {
          label: "Pocket",
          key: "pocket",
          flex: 1,
          getValue: (a) => a.stage
        },
        {
          label: "Source",
          key: "source",
          flex: 2,
          getValue: (a) => a.source
        },
        {
          label: "Due date",
          key: "dueDate",
          flex: 1,
          getValue: (a) => a.due_date ? new Date(a.due_date).toLocaleDateString() : ""
        },
        {
          label: "Reviews",
          key: "reviewsRemaining",
          flex: 1,
          getValue: (a) => String(a.all_environment_reviews_count - a.completed_environment_reviews_count)
        },
        {
          label: "Status",
          key: "status",
          flex: 1,
          getValue: (a) => STATUS_LABELS[a.status],
          color: (a) => STATUS_COLORS[a.status]
        },
        {
          label: "Assignee",
          key: "assignee",
          flex: 1,
          getValue: (a) => a.assignee?.name ?? ""
        }
      ],
      charms: [
        { label: "Name", key: "name", flex: 2, getValue: (a) => a.name },
        {
          label: "Version",
          key: "version",
          flex: 2,
          getValue: (a) => a.version
        },
        {
          label: "Track",
          key: "track",
          flex: 1,
          getValue: (a) => a.track
        },
        {
          label: "Risk",
          key: "risk",
          flex: 1,
          getValue: (a) => a.stage
        },
        {
          label: "Branch",
          key: "branch",
          flex: 1,
          getValue: (a) => a.branch
        },
        {
          label: "Due date",
          key: "dueDate",
          flex: 1,
          getValue: (a) => a.due_date ? new Date(a.due_date).toLocaleDateString() : ""
        },
        {
          label: "Reviews",
          key: "reviewsRemaining",
          flex: 1,
          getValue: (a) => String(a.all_environment_reviews_count - a.completed_environment_reviews_count)
        },
        {
          label: "Status",
          key: "status",
          flex: 1,
          getValue: (a) => STATUS_LABELS[a.status],
          color: (a) => STATUS_COLORS[a.status]
        },
        {
          label: "Assignee",
          key: "assignee",
          flex: 1,
          getValue: (a) => a.assignee?.name ?? ""
        }
      ],
      images: [
        { label: "Name", key: "name", flex: 2, getValue: (a) => a.name },
        {
          label: "Version",
          key: "version",
          flex: 1,
          getValue: (a) => a.version
        },
        { label: "OS", key: "os", flex: 1, getValue: (a) => a.os },
        {
          label: "Release",
          key: "release",
          flex: 1,
          getValue: (a) => a.release
        },
        {
          label: "Owner",
          key: "owner",
          flex: 1,
          getValue: (a) => a.owner
        },
        {
          label: "Due date",
          key: "dueDate",
          flex: 1,
          getValue: (a) => a.due_date ? new Date(a.due_date).toLocaleDateString() : ""
        },
        {
          label: "Reviews",
          key: "reviewsRemaining",
          flex: 1,
          getValue: (a) => String(a.all_environment_reviews_count - a.completed_environment_reviews_count)
        },
        {
          label: "Status",
          key: "status",
          flex: 1,
          getValue: (a) => STATUS_LABELS[a.status],
          color: (a) => STATUS_COLORS[a.status]
        },
        {
          label: "Assignee",
          key: "assignee",
          flex: 1,
          getValue: (a) => a.assignee?.name ?? ""
        }
      ]
    };
    const columns = derived(() => COLUMNS[family]);
    const sortField = derived(() => page.url.searchParams.get("sortBy") ?? "");
    const sortDir = derived(() => page.url.searchParams.get("direction") ?? "asc");
    $$renderer2.push(`<div class="table-wrapper svelte-1c2cvm9"><div class="header-row svelte-1c2cvm9"><!--[-->`);
    const each_array = ensure_array_like(columns());
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let col = each_array[$$index];
      $$renderer2.push(`<button class="header-cell svelte-1c2cvm9"${attr_style(`flex: ${stringify(col.flex)};`)}>${escape_html(col.label)} `);
      if (sortField() === col.key) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="sort-arrow svelte-1c2cvm9">${escape_html(sortDir() === "asc" ? "↑" : "↓")}</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></button>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="separator svelte-1c2cvm9"></div> <!--[-->`);
    const each_array_1 = ensure_array_like(artefacts);
    for (let $$index_2 = 0, $$length = each_array_1.length; $$index_2 < $$length; $$index_2++) {
      let artefact = each_array_1[$$index_2];
      $$renderer2.push(`<button class="data-row svelte-1c2cvm9"><!--[-->`);
      const each_array_2 = ensure_array_like(columns());
      for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
        let col = each_array_2[$$index_1];
        $$renderer2.push(`<span class="data-cell svelte-1c2cvm9"${attr_style(`flex: ${stringify(col.flex)}; ${stringify(col.color?.(artefact) ? `color: ${col.color(artefact)};` : "")}`)}>${escape_html(col.getValue(artefact))}</span>`);
      }
      $$renderer2.push(`<!--]--></button> <div class="separator svelte-1c2cvm9"></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { data } = $$props;
    const searchQuery = derived(() => page.url.searchParams.get("q") ?? "");
    const sortField = derived(() => page.url.searchParams.get("sortBy") ?? "name");
    const sortDir = derived(() => page.url.searchParams.get("direction") ?? "asc");
    const activeFilters = derived(() => {
      const filters = {};
      const defs = FAMILY_FILTERS[data.family];
      for (const def of defs) {
        const values = page.url.searchParams.getAll(def.key);
        if (values.length > 0) {
          filters[def.key] = values;
        }
      }
      return filters;
    });
    const hasActiveFilters = derived(() => Object.keys(activeFilters()).length > 0 || searchQuery() !== "");
    const searchedArtefacts = derived(() => searchQuery() ? data.artefacts.filter((a) => a.name.toLowerCase().includes(searchQuery().toLowerCase())) : data.artefacts);
    const filteredArtefacts = derived(() => {
      const defs = FAMILY_FILTERS[data.family];
      return searchedArtefacts().filter((a) => {
        for (const def of defs) {
          const active = activeFilters()[def.key];
          if (!active || active.length === 0) continue;
          const value = def.extract(a);
          if (!active.includes(value)) return false;
        }
        return true;
      });
    });
    const sortedArtefacts = derived(() => {
      const arr = [...filteredArtefacts()];
      const dir = sortDir() === "desc" ? -1 : 1;
      arr.sort((a, b) => {
        let aVal = getSortValue(a, sortField());
        let bVal = getSortValue(b, sortField());
        if (aVal === null && bVal === null) return 0;
        if (aVal === null) return 1;
        if (bVal === null) return -1;
        if (aVal < bVal) return -dir;
        if (aVal > bVal) return dir;
        return 0;
      });
      return arr;
    });
    function getSortValue(a, field) {
      switch (field) {
        case "name":
          return a.name;
        case "version":
          return a.version;
        case "track":
          return a.track;
        case "risk":
        case "pocket":
          return a.stage;
        case "branch":
          return a.branch;
        case "series":
          return a.series;
        case "repo":
          return a.repo;
        case "source":
          return a.source;
        case "os":
          return a.os;
        case "release":
          return a.release;
        case "owner":
          return a.owner;
        case "dueDate":
          return a.due_date ?? null;
        case "reviewsRemaining":
          return a.all_environment_reviews_count - a.completed_environment_reviews_count;
        case "status":
          return a.status;
        case "assignee":
          return a.assignee?.name ?? null;
        default:
          return a[field] ?? "";
      }
    }
    const artefactsByStage = derived(() => {
      const stages = FAMILY_STAGES[data.family];
      const map = /* @__PURE__ */ new Map();
      for (const stage of stages) map.set(stage, []);
      for (const a of sortedArtefacts()) {
        const bucket = map.get(a.stage);
        if (bucket) bucket.push(a);
      }
      return map;
    });
    $$renderer2.push(`<div class="dashboard svelte-o9v9y9">`);
    DashboardHeader($$renderer2, {
      family: data.family,
      filteredCount: filteredArtefacts().length,
      totalCount: data.artefacts.length
    });
    $$renderer2.push(`<!----> <div class="content-row svelte-o9v9y9"><div class="filter-toggle-area svelte-o9v9y9"><button class="filter-toggle svelte-o9v9y9" title="Toggle filters"><svg class="filter-icon svelte-o9v9y9" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6s3.72-4.8 5.74-7.39c.51-.66.04-1.61-.79-1.61H5.04c-.83 0-1.3.95-.79 1.61z"></path></svg> `);
    if (hasActiveFilters()) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="badge svelte-o9v9y9"></span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></button></div> `);
    FilterSidebar($$renderer2, {
      artefacts: data.artefacts,
      family: data.family
    });
    $$renderer2.push(`<!----> `);
    {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> <div class="body svelte-o9v9y9">`);
    if (viewModeStore.mode === "dashboard") {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="kanban svelte-o9v9y9"><!--[-->`);
      const each_array = ensure_array_like(FAMILY_STAGES[data.family]);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let stage = each_array[$$index];
        StageColumn($$renderer2, {
          stage,
          artefacts: artefactsByStage().get(stage) ?? [],
          family: data.family
        });
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      ArtefactTable($$renderer2, { artefacts: sortedArtefacts(), family: data.family });
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
  });
}
export {
  _page as default
};
