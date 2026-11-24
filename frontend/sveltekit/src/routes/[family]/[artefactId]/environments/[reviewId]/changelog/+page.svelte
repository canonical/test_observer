<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
     SPDX-License-Identifier: Apache-2.0 -->
<script lang="ts">
  import ChangelogPage from "$lib/components/changelog/ChangelogPage.svelte";
  let { data } = $props();
</script>

<ChangelogPage
  family={data.family}
  artefactId={data.artefactId}
  reviewId={data.reviewId}
/>
