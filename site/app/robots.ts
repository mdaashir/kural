import type { MetadataRoute } from "next";
import { base } from "../lib/site";
export const dynamic = "force-static";
export default function robots(): MetadataRoute.Robots { return { rules: { userAgent: "*", allow: "/kural/" }, sitemap: `${base}/sitemap.xml` }; }
