import { defineStore } from "pinia";
import { ref } from "vue";

import { getHealth } from "../api";

export const useSystemStore = defineStore("system", () => {
  const apiStatus = ref("checking");
  const apiVersion = ref("");

  async function checkApi() {
    try {
      const health = await getHealth();
      apiStatus.value = health.status === "ok" ? "online" : "degraded";
      apiVersion.value = health.version;
    } catch {
      apiStatus.value = "offline";
      apiVersion.value = "";
    }
  }

  return {
    apiStatus,
    apiVersion,
    checkApi,
  };
});
