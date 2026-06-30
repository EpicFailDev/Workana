/// <reference types="vitest" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import { fileURLToPath, URL } from "url";

export default defineConfig(({ mode }) => {
  // Carrega as variáveis de ambiente com base no diretório atual
  const env = loadEnv(mode, process.cwd(), "");

  // Validar variáveis críticas do Supabase durante o build em produção
  const isProdBuild = mode === "production" || process.env.NODE_ENV === "production";
  if (isProdBuild) {
    if (!env.VITE_SUPABASE_URL) {
      throw new Error("❌ ERRO NO BUILD: A variável de ambiente VITE_SUPABASE_URL não está definida!");
    }
    if (!env.VITE_SUPABASE_PUBLISHABLE_KEY) {
      throw new Error("❌ ERRO NO BUILD: A variável de ambiente VITE_SUPABASE_PUBLISHABLE_KEY não está definida!");
    }
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      host: true,
      port: 8080,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
          secure: false,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
    },
  };
});
