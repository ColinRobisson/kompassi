const withNextIntl = require("next-intl/plugin")();

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  serverActions: {
    bodySizeLimit: "100mb",
  },
};

module.exports = withNextIntl(nextConfig);
