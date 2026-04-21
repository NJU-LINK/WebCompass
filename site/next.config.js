/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === "production";
const basePath = isProduction ? "/WebCompass" : "";

const nextConfig = {
  output: "export",
  trailingSlash: true,
  basePath,
  assetPrefix: isProduction ? "/WebCompass" : undefined,
  images: {
    unoptimized: true
  }
};

module.exports = nextConfig;
