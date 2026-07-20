<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import ErrorPopup from '$lib/components/ErrorPopup.svelte';
  import { errorStore } from '$lib/stores/error.svelte';
</script>

<style global>
  @import '../app.css';
</style>

<h1>Test Observer</h1>
<p>SvelteKit frontend — work in progress.</p>

<button onclick={() => errorStore.set('Something went wrong: could not connect to the Test Observer API.')}>
  Show error popup
</button>

<ErrorPopup />
