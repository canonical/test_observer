import { error } from "@sveltejs/kit";
const FAMILIES = ["snaps", "debs", "charms", "images"];
const load = ({ params }) => {
  if (!FAMILIES.includes(params.family)) {
    error(404, `Unknown family: ${params.family}`);
  }
  return { family: params.family };
};
export {
  load
};
