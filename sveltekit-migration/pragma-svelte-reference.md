# Pragma Svelte Quick Reference

> Reference for agents working on the test-observer SvelteKit redesign.
> Package: `@canonical/svelte-ds-app-launchpad` v0.27.0
> Source: https://github.com/canonical/pragma/tree/main/packages/svelte/ds-app-launchpad

---

## Installation

```bash
bun add @canonical/svelte-ds-app-launchpad
# Automatically installs:
#   @canonical/svelte-icons        (icons)
#   @canonical/launchpad-design-tokens  (CSS tokens)
#   @floating-ui/dom               (floating positioning)
```

**Do NOT install separately:**
- `@canonical/styles` — React/vanilla DS aggregator, not for Svelte
- `@canonical/ds-assets` — React icon package, not for Svelte

---

## Style Setup

Import styles **in `src/routes/+layout.svelte`**, not in a global CSS file:

```svelte
<script lang="ts">
  import "@canonical/svelte-ds-app-launchpad/styles.css";
  import "@canonical/launchpad-design-tokens/dist/css/dimension/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/typography/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/opacity/opacity.css";
  import "@canonical/launchpad-design-tokens/dist/css/transition/preferred.css";
  import "@canonical/launchpad-design-tokens/dist/css/color/light.css";
  // Use dark.css or system.css for dark mode support
</script>
```

---

## Available Components

All exported from `@canonical/svelte-ds-app-launchpad`:

```svelte
<script lang="ts">
  import {
    Badge,
    Breadcrumbs,
    Button,
    Checkbox,
    Chip,
    DateTime,
    DescriptionList,
    Link,
    Modal,
    NumberInput,
    Popover,
    Radio,
    RelativeDateTime,
    SearchBox,
    Select,
    SideNavigation,
    SidePanel,
    Spinner,
    Switch,
    Table,
    TextInput,
    Textarea,
    Timeline,
    Tooltip,
    UserAvatar,
  } from "@canonical/svelte-ds-app-launchpad";
</script>
```

> **Note:** The navigation component is `SideNavigation`, **not** `Navigation`.

---

## Icons

```svelte
<script lang="ts">
  import { SomeIcon, AnotherIcon } from "@canonical/svelte-icons";
</script>

<SomeIcon />
```

Browse available icons in the Pragma Storybook or at:
https://github.com/canonical/pragma/tree/main/packages/svelte/ds-app-launchpad/src/lib/components/icons

---

## CSS Custom Properties

Custom component styles use CSS custom properties from the launchpad design tokens.
Browse available tokens at:
`node_modules/@canonical/launchpad-design-tokens/dist/css/`

Key token files:
- `dimension/responsive.css` — spacing, sizing (`--spacing-*`, `--size-*`)
- `typography/responsive.css` — font sizes, line heights
- `color/light.css` — colour palette (`--color-background`, `--color-text`, etc.)
- `opacity/opacity.css` — opacity levels

Example custom component CSS:
```css
.ds.artefact-card {
  padding: var(--spacing-2);
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-small);
}

.ds.artefact-card.negative {
  border-color: var(--color-negative-border);
}
```

---

## Modifier Families

Available severity modifiers for components that support them (e.g. Badge, Chip):

| Modifier | Meaning | Usage |
|---|---|---|
| `positive` | Success / approved | Artefact status: APPROVED |
| `negative` | Error / failed | Artefact status: MARKED_AS_FAILED |
| `caution` | Warning | Artefact status: in-progress with issues |
| `neutral` | Default / undecided | Artefact status: UNDECIDED |
| `information` | Informational | Notifications, hints |

Density modifiers: `compact` | `comfortable`

---

## Component Examples

### SideNavigation

```svelte
<script lang="ts">
  import { SideNavigation } from "@canonical/svelte-ds-app-launchpad";

  // Nav items are ALWAYS derived from config.tabs — never hardcoded
  const { tabs, currentPath } = $props<{ tabs: string[]; currentPath: string }>();

  const navItems = $derived([
    ...tabs.map(family => ({
      href: `/${family}`,
      label: family.charAt(0).toUpperCase() + family.slice(1) + "s",
      active: currentPath.startsWith(`/${family}`),
    })),
    { href: "/test-results", label: "Test Results", active: currentPath === "/test-results" },
    { href: "/issues", label: "Issues", active: currentPath.startsWith("/issues") },
    { href: "/notifications", label: "Notifications", active: currentPath === "/notifications" },
  ]);
</script>

<SideNavigation items={navItems} />
```

### Badge with severity

```svelte
<script lang="ts">
  import { Badge } from "@canonical/svelte-ds-app-launchpad";
  import type { ArtefactStatus } from "$lib/types/artefact.js";

  const { status }: { status: ArtefactStatus } = $props();

  const severity = $derived(
    status === "APPROVED" ? "positive"
    : status === "MARKED_AS_FAILED" ? "negative"
    : "neutral"
  );
</script>

<Badge {severity}>{status}</Badge>
```

### Modal (dialog)

```svelte
<script lang="ts">
  import { Modal, Button } from "@canonical/svelte-ds-app-launchpad";

  let open = $state(false);
</script>

<Button onclick={() => open = true}>Open dialog</Button>
<Modal bind:open title="Confirm action">
  <p>Are you sure?</p>
  {#snippet footer()}
    <Button onclick={() => open = false}>Cancel</Button>
    <Button appearance="positive" onclick={handleConfirm}>Confirm</Button>
  {/snippet}
</Modal>
```

### Table

```svelte
<script lang="ts">
  import { Table } from "@canonical/svelte-ds-app-launchpad";
</script>

<Table
  headers={["Name", "Version", "Status"]}
  rows={artefacts.map(a => [a.name, a.version, a.status])}
/>
```

---

## Development: Storybook

To browse components interactively:

```bash
git clone https://github.com/canonical/pragma /tmp/pragma
cd /tmp/pragma && bun install
cd packages/svelte/ds-app-launchpad
bunx playwright install  # needed for browser tests
bun run storybook        # opens http://localhost:6006
```

---

## Pragma Class Naming Convention

Custom components follow the `ds` namespace pattern (mirrors Pragma React):

```svelte
<!-- Component root: "ds <component-name>" -->
<div class="ds artefact-card {className}">
  <!-- Child elements: "ds <component-name>__<element>" -->
  <span class="ds artefact-card__name">{name}</span>
  <!-- Modifier classes added to root: "ds <component-name> <modifier>" -->
</div>
```

```css
/* styles.css */
.ds.artefact-card { ... }
.ds.artefact-card__name { ... }
.ds.artefact-card.negative { ... }
.ds.artefact-card.compact { ... }
```

---

## Architecture Validation

```bash
# In a component library package (not typically run for app-level code):
bun run check:webarchitect   # uses 'package-svelte' ruleset

# For the SvelteKit app, the primary checks are:
bun run svelte-check   # type safety
bun run biome check .  # lint + format
```
