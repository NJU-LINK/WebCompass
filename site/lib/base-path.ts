const productionBasePath = "/WebCompass";
const isProduction = process.env.NODE_ENV === "production";

export const basePath = isProduction ? productionBasePath : "";

export function withBasePath(path: string) {
  if (!path.startsWith("/")) return `${basePath}/${path}`;
  if (!basePath) return path;
  if (path.startsWith(`${basePath}/`) || path === basePath) return path;
  return `${basePath}${path}`;
}
