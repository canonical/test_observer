<template>
  <div>
    <nav class="navbar">
      <div class="container navbar-content">
        <img src="/vue_poc/logo.png" alt="Logo" class="navbar-logo" />
        <NuxtLink to="/" class="navbar-link">Snap Testing</NuxtLink>
        <NuxtLink to="/debs" class="navbar-link">Deb Testing</NuxtLink>
        <NuxtLink to="/charms" class="navbar-link">Charm Testing</NuxtLink>
        <NuxtLink to="/images" class="navbar-link">Image Testing</NuxtLink>
        <div class="navbar-spacer"></div>
        <NuxtLink to="/search" class="navbar-link">Search</NuxtLink>
        <NuxtLink to="/issues" class="navbar-link">Issues</NuxtLink>
        <div class="navbar-link">Help</div>
      </div>
    </nav>
    <main class="container">
      <slot />
    </main>
  </div>
</template>
