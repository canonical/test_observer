<script lang="ts">
  interface Props {
    source: string;
    project: string;
  }

  let { source, project }: Props = $props();
</script>

<div class="issue-group-header">
  <span class="source-label">{source.toUpperCase()}</span>
  <span class="project-label">{project || '(no project)'}</span>
</div>

<style>
  .issue-group-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 12px 0 6px;
    border-bottom: 1px solid #e0e0e0;
  }

  .source-label {
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1px;
    color: #333;
  }

  .project-label {
    font-size: 13px;
    color: #666;
  }
</style>
