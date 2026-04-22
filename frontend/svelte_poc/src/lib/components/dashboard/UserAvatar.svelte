<script lang="ts">
  import { userInitials } from '$lib/types';
  import type { User } from '$lib/types';

  let { user, completed, total }: {
    user: User | null;
    completed: number;
    total: number;
  } = $props();

  const initials = $derived(user ? userInitials(user.name) : '');
  const progress = $derived(total > 0 ? completed / total : 0);
  const circumference = 2 * Math.PI * 18;
  const dashOffset = $derived(circumference * (1 - progress));

  // Flutter accent colors: redAccent, yellowAccent, blueAccent, orangeAccent, greenAccent, purpleAccent
  const COLORS = ['#FF5252', '#FFFF00', '#448AFF', '#FFAB40', '#69F0AE', '#E040FB'];
  const avatarColor = $derived(
    user
      ? COLORS[Math.abs(user.id) % COLORS.length]
      : COLORS[5] // purpleAccent for unassigned (matches Flutter: id=-1 % 6 = 5)
  );

  // Progress arc color: same hue but 0.2 lightness darker (matches Flutter _progressColor)
  function darkenColor(hex: string): string {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      else if (max === g) h = ((b - r) / d + 2) / 6;
      else h = ((r - g) / d + 4) / 6;
    }
    l = Math.max(0, l - 0.2);
    // HSL to hex
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    const q2 = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p2 = 2 * l - q2;
    const toHex = (v: number) => Math.round(v * 255).toString(16).padStart(2, '0');
    return `#${toHex(hue2rgb(p2, q2, h + 1/3))}${toHex(hue2rgb(p2, q2, h))}${toHex(hue2rgb(p2, q2, h - 1/3))}`;
  }

  const progressColor = $derived(darkenColor(avatarColor));
</script>

<div class="avatar-wrapper" title="{user?.name ?? 'Unassigned'} ({completed}/{total} reviews)">
  <svg width="44" height="44" viewBox="0 0 44 44">
    <circle cx="22" cy="22" r="18" fill="none" stroke={avatarColor} stroke-width="2.5" />
    <circle
      cx="22" cy="22" r="18"
      fill="none"
      stroke={progressColor}
      stroke-width="2.5"
      stroke-dasharray={circumference}
      stroke-dashoffset={dashOffset}
      stroke-linecap="round"
      transform="rotate(-90 22 22)"
    />
  </svg>
  {#if user}
    <div class="initials" style="background-color: {avatarColor};">{initials}</div>
  {/if}
</div>

<style>
  .avatar-wrapper {
    position: relative;
    width: 44px;
    height: 44px;
    flex-shrink: 0;
  }

  .avatar-wrapper svg {
    position: absolute;
    top: 0;
    left: 0;
  }

  .initials {
    position: absolute;
    top: 5px;
    left: 5px;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
  }
</style>
