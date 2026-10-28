/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: "standalone",
  experimental: {
    turbo: {
      rules: {},
    },
  },
};

export default nextConfig;
