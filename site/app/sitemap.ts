import type { MetadataRoute } from "next";
import { base, routes } from "../lib/site";
export const dynamic = "force-static";
export default function sitemap(): MetadataRoute.Sitemap { return routes.map(path => ({ url: `${base}${path}` })); }
