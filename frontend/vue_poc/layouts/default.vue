<template>
  <div class="min-h-screen flex flex-col bg-gray-50 text-gray-900 font-sans">
    <AppHeader />
    <main class="flex-grow w-full max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
// Layout logic here if needed
</script>
