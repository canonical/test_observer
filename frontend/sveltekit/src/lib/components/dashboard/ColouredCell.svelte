<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<!-- A component rather than a {#snippet}: the grid's cell renderers are built
     in <script> scope, where markup snippets are not in lexical scope. -->
<script lang="ts">
  let { text, color }: { text: string; color: string } = $props();
</script>

<span style="color: {color}">{text}</span>
