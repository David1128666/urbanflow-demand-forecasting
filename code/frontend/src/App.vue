<script setup>
import {
  BrainCircuit,
  ChartLine,
  ExternalLink,
  Languages,
  LayoutDashboard,
  Route,
} from "@lucide/vue";
import { RouterLink, RouterView } from "vue-router";

import { localeLabel, t, toggleLocale } from "./i18n";
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">UF</span>
        <span>UrbanFlow</span>
      </RouterLink>
      <nav class="nav">
        <RouterLink to="/">
          <LayoutDashboard :size="16" />
          {{ t("nav.overview") }}
        </RouterLink>
        <RouterLink to="/forecast">
          <ChartLine :size="16" />
          {{ t("nav.forecast") }}
        </RouterLink>
        <RouterLink to="/models">
          <BrainCircuit :size="16" />
          {{ t("nav.models") }}
        </RouterLink>
        <RouterLink to="/dispatch">
          <Route :size="16" />
          {{ t("nav.dispatch") }}
        </RouterLink>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
          <ExternalLink :size="16" />
          {{ t("nav.docs") }}
        </a>
        <button class="nav-language" type="button" @click="toggleLocale">
          <Languages :size="16" />
          {{ localeLabel }}
        </button>
      </nav>
    </header>

    <main class="page">
      <RouterView />
    </main>
  </div>
</template>
