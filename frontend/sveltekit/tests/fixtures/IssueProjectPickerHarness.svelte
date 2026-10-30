<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script>
  import Picker from "../../src/lib/components/issues/IssueProjectPicker.svelte";
  let { ontoggle } = $props();
  let selected = $state(["unloaded/project"]);
  const options = ["Alpha/project", "Beta/project", "unloaded/project"];
</script>

<Picker
  {options}
  {selected}
  ontoggle={(project, checked) => {
    selected = checked
      ? [...new Set([...selected, project])]
      : selected.filter((item) => item !== project);
    return ontoggle?.(project, checked);
  }}
>
  <p id="project-discovery-help">Fixture discovery is partial.</p>
</Picker>
