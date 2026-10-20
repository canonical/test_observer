<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script>
  import SearchResultDetails from "../../../src/lib/components/search/SearchResultDetails.svelte";
  import { largeResult, emptyResult, families } from "./data.js";

  // Only the harness controls which loaded object to present. No transport,
  // search-store overrides, alternate modal implementation or fixture styles.
  /** @type {import('../../../src/lib/testResultsSearch').SearchResult | null} */
  let result = $state(null);
</script>

<h1>Actual Details component — synthetic read-only browser fixture</h1>
<p>Not live backend or production-data evidence.</p>
<button onclick={() => (result = largeResult)}
  >Open representative details</button
>
<button onclick={() => (result = emptyResult)}>Open empty details</button>
<SearchResultDetails
  {result}
  {families}
  base="/fixture-base"
  onclose={() => (result = null)}
/>
