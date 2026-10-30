<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script>
  import { attachmentRuleAttention } from "../src/lib/attachmentRuleAttention";
  let { attention } = $props();
</script>

<details use:attachmentRuleAttention={attention}>
  <summary>Attachment Rule #14</summary>
  <p>Rule criteria</p>
</details>
