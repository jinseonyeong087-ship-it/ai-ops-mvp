import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 워크스페이스 루트 오탐지 경고 방지: 이 프로젝트(frontend)를 Turbopack 루트로 고정
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
