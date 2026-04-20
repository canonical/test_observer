<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import ErrorPopup from '$lib/components/ErrorPopup.svelte';
  import { userStore } from '$lib/stores/user.svelte';
  import '../app.css';

  let { data, children } = $props();

  $effect(() => {
    userStore.set(data.user);
  });
</script>

<div class="app-shell">
  <Navbar />
  <main class="main-content">
    {@render children()}
  </main>
  <ErrorPopup />
</div>

<style>
  .app-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    flex: 1;
    width: 100%;
    max-width: 1800px;
    margin: 0 auto;
    padding: 16px 32px;
  }
</style>
