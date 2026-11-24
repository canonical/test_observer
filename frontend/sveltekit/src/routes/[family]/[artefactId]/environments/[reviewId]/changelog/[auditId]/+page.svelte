<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
     SPDX-License-Identifier: Apache-2.0 -->
<script lang="ts">
  import ChangelogDetailPage from "$lib/components/changelog/ChangelogDetailPage.svelte";
  let { data } = $props();
</script>

<ChangelogDetailPage
  family={data.family}
  artefactId={data.artefactId}
  reviewId={data.reviewId}
  auditId={data.auditId}
/>
