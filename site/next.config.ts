import type { NextConfig } from "next";

const config: NextConfig = {
  output: "export",
  basePath: "/kural",
  trailingSlash: true,
  images: { unoptimized: true },
};
export default config;
