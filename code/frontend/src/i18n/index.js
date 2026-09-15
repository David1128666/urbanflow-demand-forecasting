import { computed, ref } from "vue";

import en from "../locales/en";
import zhCN from "../locales/zh-CN";


const messages = {
  en,
  "zh-CN": zhCN,
};
const environmentLocale = import.meta.env.VITE_APP_LANGUAGE || "en";
const storedLocale =
  typeof window !== "undefined"
    ? window.localStorage.getItem("urbanflow-locale")
    : null;

export const locale = ref(
  messages[storedLocale] ? storedLocale : environmentLocale,
);
if (typeof window !== "undefined") {
  window.localStorage.setItem("urbanflow-locale", locale.value);
  document.documentElement.lang = locale.value;
  document.title =
    locale.value === "en"
      ? "UrbanFlow Demand Forecasting"
      : "UrbanFlow 城市需求预测";
}
export const localeLabel = computed(() =>
  locale.value === "en" ? "中文" : "EN",
);

export function t(key, params = {}) {
  const dictionary = messages[locale.value] || messages.en;
  const template = dictionary[key] || messages.en[key] || key;
  return template.replace(/\{(\w+)\}/g, (_, name) =>
    params[name] === null || params[name] === undefined
      ? ""
      : String(params[name]),
  );
}

export function setLocale(nextLocale) {
  if (!messages[nextLocale]) {
    return;
  }
  locale.value = nextLocale;
  if (typeof window !== "undefined") {
    window.localStorage.setItem("urbanflow-locale", nextLocale);
    document.documentElement.lang = nextLocale;
    document.title =
      nextLocale === "en"
        ? "UrbanFlow Demand Forecasting"
        : "UrbanFlow 城市需求预测";
  }
}

export function toggleLocale() {
  setLocale(locale.value === "en" ? "zh-CN" : "en");
}
