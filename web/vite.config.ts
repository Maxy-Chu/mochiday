import {
  vitePlugin as remix,
  cloudflareDevProxyVitePlugin as remixCloudflareDevProxy,
} from "@remix-run/dev";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import { getLoadContext } from "./load-context";
import path from "path";

export default defineConfig({
  // MX ADDED
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "app"),
    },
  },
  // END OF MX ADDED
  optimizeDeps: {
    include: ["esm-dep > cjs-dep"],
  },
  plugins: [
    remixCloudflareDevProxy({ getLoadContext }),
    remix(),
    tsconfigPaths(),
  ],
});
