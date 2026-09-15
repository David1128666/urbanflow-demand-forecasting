<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import { getDashboardSummary } from "../api";
import EChart from "../components/EChart.vue";
import { t } from "../i18n";
import { useSystemStore } from "../stores/system";

const system = useSystemStore();
const summary = ref(null);
const loading = ref(false);
const error = ref("");

const apiStatusText = computed(() => {
  const labels = {
    checking: t("common.status.checking"),
    online: t("common.status.online"),
    degraded: t("common.status.degraded"),
    offline: t("common.status.offline"),
  };
  return labels[system.apiStatus] || t("common.status.unknown");
});

const forecastSummary = computed(() => summary.value?.forecast_summary || {});
const inventorySummary = computed(() => summary.value?.inventory_summary || {});
const dispatchSummary = computed(() => summary.value?.dispatch_summary || {});
const latestRun = computed(() => summary.value?.latest_run || {});
const topStations = computed(() => summary.value?.top_stations || []);
const peakPeriods = computed(() => summary.value?.peak_periods || []);
let refreshTimer;
const consistencyMessage = computed(() => {
  const status = summary.value?.run_consistency?.status;
  return status ? t(`home.consistency.${status}`) : "";
});

const topStationsOption = computed(() => {
  const rows = [...topStations.value].reverse();
  return {
    grid: { left: 72, right: 24, top: 20, bottom: 34 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      name: t("home.ranking.axis"),
      splitLine: { lineStyle: { color: "#e8edf1" } },
    },
    yAxis: {
      type: "category",
      data: rows.map(
        (row) => `${row.station_id} · ${row.station_name || "--"}`,
      ),
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: rows.map((row) => row.total_demand),
        itemStyle: { color: "#2b6f71", borderRadius: [0, 5, 5, 0] },
        barWidth: 14,
      },
    ],
  };
});

const peakPeriodsOption = computed(() => ({
  grid: { left: 48, right: 20, top: 28, bottom: 52 },
  tooltip: { trigger: "axis" },
  xAxis: {
    type: "category",
    data: peakPeriods.value.map((row) =>
      formatTime(row.window_start, true),
    ),
    axisLabel: { rotate: 20, color: "#667582" },
    axisLine: { lineStyle: { color: "#cfd8df" } },
  },
  yAxis: {
    type: "value",
    name: t("home.peak.axis"),
    splitLine: { lineStyle: { color: "#e8edf1" } },
  },
  series: [
    {
      type: "line",
      smooth: true,
      symbolSize: 8,
      data: peakPeriods.value.map((row) => row.aggregate_demand),
      lineStyle: { color: "#e09a2d", width: 3 },
      itemStyle: { color: "#e09a2d" },
      areaStyle: { color: "rgba(224, 154, 45, 0.14)" },
    },
  ],
}));

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    summary.value = await getDashboardSummary();
    await system.checkApi();
  } catch (requestError) {
    error.value = requestError.message || t("home.error");
  } finally {
    loading.value = false;
  }
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "--";
  }
  return new Intl.NumberFormat("zh-CN").format(value);
}

function formatTime(value, compact = false) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  return new Intl.DateTimeFormat("zh-CN", {
    month: compact ? "2-digit" : undefined,
    day: compact ? "2-digit" : undefined,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

onMounted(() => {
  loadData();
  refreshTimer = window.setInterval(loadData, 10000);
});

onBeforeUnmount(() => {
  window.clearInterval(refreshTimer);
});
</script>

<template>
  <section class="page-heading">
    <div>
      <p class="eyebrow">{{ t("home.eyebrow") }}</p>
      <h1>{{ t("home.title") }}</h1>
      <p class="supporting">{{ t("home.subtitle") }}</p>
    </div>
    <div class="heading-actions">
      <span class="status-pill" :data-status="system.apiStatus">
        API {{ apiStatusText }}
      </span>
      <span class="panel-tag">{{ t("home.dataMode") }}</span>
      <button class="icon-button" type="button" :disabled="loading" @click="loadData">
        <RefreshCw :size="17" :class="{ spinning: loading }" />
        <span>{{ t("common.refresh") }}</span>
      </button>
    </div>
  </section>

  <div v-if="error" class="alert alert-error">{{ error }}</div>
  <div
    v-if="summary?.run_consistency && !summary.run_consistency.is_ready"
    class="alert"
    :class="
      summary.run_consistency.status === 'updating'
        ? 'alert-info'
        : 'alert-warning'
    "
  >
    {{ consistencyMessage }}
  </div>

  <section class="metric-grid">
    <article class="metric-card">
      <span class="metric-label">{{ t("home.metric.stations") }}</span>
      <strong>{{ formatNumber(summary?.station_count) }}</strong>
      <span>{{ t("home.metric.stationsHelp") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("home.metric.twoHourOrders") }}</span>
      <strong>{{ formatNumber(dispatchSummary.near_term_orders) }}</strong>
      <span>{{ t("home.metric.twoHourOrdersHelp") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("home.metric.intervention") }}</span>
      <strong>{{ formatNumber(dispatchSummary.target_station_count) }}</strong>
      <span>{{ t("home.metric.interventionHelp") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("home.metric.recommendedMoves") }}</span>
      <strong>{{ formatNumber(dispatchSummary.total_quantity) }}</strong>
      <span>
        {{
          t("home.metric.recommendedMovesHelp", {
            count: dispatchSummary.recommendation_count ?? 0,
          })
        }}
      </span>
    </article>
  </section>

  <section class="dashboard-grid">
    <article class="panel">
      <div class="panel-heading">
        <div>
          <h2>{{ t("home.ranking.title") }}</h2>
          <p>{{ t("home.ranking.subtitle") }}</p>
        </div>
        <span class="panel-tag">Top 10</span>
      </div>
      <EChart :option="topStationsOption" height="360px" />
    </article>

    <article class="panel">
      <div class="panel-heading">
        <div>
          <h2>{{ t("home.peak.title") }}</h2>
          <p>{{ t("home.peak.subtitle") }}</p>
        </div>
      </div>
      <EChart :option="peakPeriodsOption" height="360px" />
    </article>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("home.dispatch.title") }}</h2>
        <p>{{ t("home.dispatch.subtitle") }}</p>
      </div>
      <RouterLink class="text-link" to="/dispatch">
        {{ t("home.dispatch.view") }}
      </RouterLink>
    </div>
    <div class="detail-grid">
      <div>
        <span class="detail-label">{{ t("home.dispatch.window") }}</span>
        <strong>
          {{ formatTime(dispatchSummary.decision_window_start) }}
          {{ t("common.to") }}
          {{ formatTime(dispatchSummary.decision_window_end) }}
        </strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.dispatch.riskOrders") }}</span>
        <strong>{{ dispatchSummary.total_shortage_before ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.dispatch.workOrders") }}</span>
        <strong>
          {{ dispatchSummary.recommendation_count ?? "--" }}
          {{ t("common.jobs") }}
        </strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.dispatch.remainingRisk") }}</span>
        <strong>{{ dispatchSummary.total_shortage_after ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.dispatch.reduction") }}</span>
        <strong>{{ dispatchSummary.shortage_reduction_pct ?? "--" }}%</strong>
      </div>
    </div>
    <p class="data-note">{{ dispatchSummary.result_basis }}</p>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("home.glossary.title") }}</h2>
        <p>{{ t("home.glossary.subtitle") }}</p>
      </div>
    </div>
    <div class="definition-grid">
      <div>
        <strong>{{ t("home.glossary.demandTitle") }}</strong>
        <p>{{ t("home.glossary.demandBody") }}</p>
      </div>
      <div>
        <strong>{{ t("home.glossary.gapTitle") }}</strong>
        <p>{{ t("home.glossary.gapBody") }}</p>
      </div>
      <div>
        <strong>{{ t("home.glossary.dispatchTitle") }}</strong>
        <p>{{ t("home.glossary.dispatchBody") }}</p>
      </div>
      <div>
        <strong>{{ t("home.glossary.impactTitle") }}</strong>
        <p>{{ t("home.glossary.impactBody") }}</p>
      </div>
    </div>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("home.run.title") }}</h2>
        <p>{{ t("home.run.subtitle") }}</p>
      </div>
      <span class="panel-tag">{{ latestRun.model_version || "--" }}</span>
    </div>
    <div class="detail-grid">
      <div>
        <span class="detail-label">{{ t("home.run.id") }}</span>
        <strong>{{ latestRun.forecast_run_id ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.run.cutoff") }}</span>
        <strong>{{ formatTime(latestRun.data_cutoff) }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.run.start") }}</span>
        <strong>{{ formatTime(latestRun.forecast_start) }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.run.steps") }}</span>
        <strong>{{ latestRun.horizon_steps ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("home.run.generated") }}</span>
        <strong>{{ formatTime(latestRun.generated_at) }}</strong>
      </div>
    </div>
  </section>
</template>
