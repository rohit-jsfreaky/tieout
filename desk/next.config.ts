import type { NextConfig } from "next";

/**
 * Almost nothing to configure. The desk is a thin client: no images to optimise
 * (screenshots are live artefacts served straight from the API), no rewrites, no
 * server code beyond the one page.
 *
 * The dev indicator is off because it sits exactly where the approver field is,
 * and this screen gets recorded from `next dev`.
 */
const nextConfig: NextConfig = {
  devIndicators: false,
  // Docker: ship a self-contained server instead of the whole node_modules tree.
  // Harmless locally — `next dev` ignores it.
  output: "standalone",
};

export default nextConfig;
