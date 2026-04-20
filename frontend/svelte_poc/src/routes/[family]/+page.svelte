<script lang="ts">
  let { data } = $props();
  
  const displayNames: Record<string, string> = {
    snaps: 'Snap Testing',
    debs: 'Deb Testing',
    charms: 'Charm Testing',
    images: 'Image Testing',
  };
</script>

<h1>{displayNames[data.family] ?? data.family} Dashboard</h1>
<p>Coming soon.</p>
