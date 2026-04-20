<script lang="ts">
  let { href, title, isActive }: { href: string; title: string; isActive: boolean } = $props();
  let isHovered = $state(false);
</script>

<a
  {href}
  class="nav-entry"
  class:active={isActive}
  class:hovered={isHovered}
  onmouseenter={() => (isHovered = true)}
  onmouseleave={() => (isHovered = false)}
>
  {title}
</a>

<style>
  .nav-entry {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 16px;
    color: white;
    text-decoration: none;
    font-size: 0.95rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: background-color 0.15s;
  }

  .nav-entry.active {
    background: hsl(0 0% 25%);
    border-bottom-color: white;
  }

  .nav-entry.hovered:not(.active) {
    background: hsl(0 0% 28%);
  }
</style>
