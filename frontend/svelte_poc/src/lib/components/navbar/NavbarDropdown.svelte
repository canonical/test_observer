<script lang="ts">
  import type { Snippet } from 'svelte';
  let { label, children }: { label: string; children: Snippet } = $props();
  let isOpen = $state(false);

  function close() {
    isOpen = false;
  }

  function toggle() {
    isOpen = !isOpen;
  }
</script>

<svelte:window onclick={close} />

<div class="nav-dropdown">
  <button
    class="dropdown-trigger"
    onclick={(e) => { e.stopPropagation(); toggle(); }}
    aria-expanded={isOpen}
  >
    {label} ▾
  </button>
  {#if isOpen}
    <div class="dropdown-panel" onclick={(e) => e.stopPropagation()}>
      {@render children()}
    </div>
  {/if}
</div>

<style>
  .nav-dropdown {
    position: relative;
    display: flex;
    align-items: center;
    height: 100%;
  }

  .dropdown-trigger {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 16px;
    color: white;
    font-size: 0.95rem;
    font-weight: 500;
    background: transparent;
    border: none;
    cursor: pointer;
  }

  .dropdown-trigger:hover {
    background: hsl(0 0% 28%);
  }

  .dropdown-panel {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 160px;
    background: #333;
    border: 1px solid #444;
    z-index: 100;
    display: flex;
    flex-direction: column;
  }

  .dropdown-panel :global(a),
  .dropdown-panel :global(button) {
    display: block;
    padding: 10px 16px;
    color: white;
    text-decoration: none;
    font-size: 0.9rem;
    text-align: left;
    background: transparent;
    border: none;
    cursor: pointer;
  }

  .dropdown-panel :global(a:hover),
  .dropdown-panel :global(button:hover) {
    background: hsl(0 0% 28%);
  }
</style>
