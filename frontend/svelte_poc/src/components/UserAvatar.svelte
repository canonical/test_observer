<script>
  export let user = null;
  export let allEnvironmentReviewsCount;
  export let completedEnvironmentReviewsCount;

  $: isEmpty = !user || !user.name;
  
  $: initials = (() => {
    if (isEmpty) return '';
    
    const names = user.name.split(' ').filter(n => n.length > 0);
    if (names.length === 0) return '';
    if (names.length === 1) {
      return names[0][0].toUpperCase();
    }
    return names[0][0].toUpperCase() + names[names.length - 1][0].toUpperCase();
  })();

  $: ratioCompleted = allEnvironmentReviewsCount === 0 ? 0 : completedEnvironmentReviewsCount / allEnvironmentReviewsCount;

  $: avatarColor = (() => {
    const colors = [
      '#FF5252', // redAccent
      '#FFFF00', // yellowAccent
      '#448AFF', // blueAccent
      '#FF9800', // orangeAccent
      '#69F0AE', // greenAccent
      '#E040FB', // purpleAccent
    ];
    const userId = user?.id || 0;
    return colors[userId % colors.length];
  })();

  $: progressColor = adjustLightness(avatarColor, -0.2);

  $: circumference = 2 * Math.PI * 19.5;

  $: progressOffset = circumference * (1 - ratioCompleted);

  $: tooltipMessage = (() => {
    const percentage = Math.round(ratioCompleted * 100);
    let result = `Completed: ${completedEnvironmentReviewsCount} / ${allEnvironmentReviewsCount} (${percentage}%)`;
    
    if (isEmpty) {
      result = `No reviewer assigned\n${result}`;
    } else {
      if (user.launchpad_handle) {
        result = `${user.launchpad_handle}\n${result}`;
      }
      result = `${user.name}\n${result}`;
    }
    
    return result;
  })();

  function adjustLightness(hexColor, adjustment) {
    // Convert hex to RGB
    const r = parseInt(hexColor.slice(1, 3), 16) / 255;
    const g = parseInt(hexColor.slice(3, 5), 16) / 255;
    const b = parseInt(hexColor.slice(5, 7), 16) / 255;
    
    // Convert RGB to HSL
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s;
    const l = (max + min) / 2;
    
    if (max === min) {
      h = s = 0;
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }
    
    // Adjust lightness
    const newL = Math.max(0, Math.min(1, l + adjustment));
    
    // Convert HSL back to RGB
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    
    let newR, newG, newB;
    if (s === 0) {
      newR = newG = newB = newL;
    } else {
      const q = newL < 0.5 ? newL * (1 + s) : newL + s - newL * s;
      const p = 2 * newL - q;
      newR = hue2rgb(p, q, h + 1/3);
      newG = hue2rgb(p, q, h);
      newB = hue2rgb(p, q, h - 1/3);
    }
    
    // Convert back to hex
    const toHex = (val) => {
      const hex = Math.round(val * 255).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
  }
</script>

<div class="user-avatar" title={tooltipMessage}>
  <svg class="avatar-svg" width="43" height="43" viewBox="0 0 43 43">
    <!-- Background circle for progress indicator -->
    <circle
      cx="21.5"
      cy="21.5"
      r="19.5"
      fill="none"
      stroke={avatarColor}
      stroke-width="3"
      opacity="0.3"
    />
    <!-- Progress arc -->
    <circle
      cx="21.5"
      cy="21.5"
      r="19.5"
      fill="none"
      stroke={progressColor}
      stroke-width="3"
      stroke-linecap="round"
      stroke-dasharray={circumference}
      stroke-dashoffset={progressOffset}
      transform="rotate(-90 21.5 21.5)"
    />
    <!-- Inner circle with background color -->
    {#if !isEmpty}
      <circle
        cx="21.5"
        cy="21.5"
        r="15"
        fill={avatarColor}
      />
    {/if}
  </svg>
  <!-- Initials text -->
  {#if !isEmpty}
    <span class="initials">{initials}</span>
  {/if}
</div>

<style>
.user-avatar {
  position: relative;
  width: 43px;
  height: 43px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: default;
}

.avatar-svg {
  position: absolute;
  top: 0;
  left: 0;
}

.initials {
  position: relative;
  z-index: 1;
  font-size: 14px;
  font-weight: 700;
  color: #000;
  user-select: none;
}
</style>
