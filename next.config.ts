import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: "http://ai-hiring-assistant.railway.internal:8080/api/:path*",
            },
        ];
    },
};

export default nextConfig;
