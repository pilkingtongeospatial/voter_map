import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/js/**/*.test.js"],
    // Pure logic tests — no DOM, so node environment is the right default.
    // Switch to "jsdom" if a future test needs document/window.
    environment: "node",
    reporters: ["verbose"],
  },
});
