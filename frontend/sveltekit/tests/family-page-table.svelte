<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  let {
    artefacts,
    family,
    filtered = $bindable(false),
    exportAvailable = $bindable(false),
  } = $props<{
    artefacts: { id: number }[];
    family: { api_name: string };
    filtered?: boolean;
    exportAvailable?: boolean;
  }>();
</script>

<div
  class="artefact-table"
  data-family={family.api_name}
  data-count={artefacts.length}
  data-filtered={filtered}
  data-export-available={exportAvailable}
>
  {artefacts.length} rows
</div>
