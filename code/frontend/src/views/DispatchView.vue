<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import { getDispatchRecommendations, getDispatchSummary } from "../api";
import EChart from "../components/EChart.vue";
import { locale, t } from "../i18n";

const summary = ref(null);
const recommendations = ref([]);
const loading = ref(false);
const error = ref("");
let refreshTimer;
const priorityRecommendations = computed(() =>
  recommendations.value.slice(0, 3),
);

const dispatchOption = computed(() => {
  const rows = [...recommendations.value].sort(
    (left, right) =>
      Number(left.recommended_quantity) - Number(right.recommended_quantity),
  );
  return {
    grid: { left: 86, right: 26, top: 22, bottom: 38 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      name: t("dispatch.chart.axis"),
      splitLine: { lineStyle: { color: "#e8edf1" } },
    },
    yAxis: {
      type: "category",
      data: rows.map(
        (row) =>
          `${row.from_station_name || row.from_station_id} → ` +
          `${row.to_station_name || row.to_station_id}`,
      ),
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: rows.map((row) => row.recommended_quantity),
        itemStyle: { color: "#2b6f71", borderRadius: [0, 5, 5, 0] },
        barWidth: 14,
      },
    ],
  };
});

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    const [summaryPayload, recommendationPayload] = await Promise.all([
      getDispatchSummary(),
      getDispatchRecommendations({ limit: 200 }),
    ]);
    summary.value = summaryPayload;
    recommendations.value = recommendationPayload;
  } catch (requestError) {
    error.value = requestError.message || t("dispatch.error");
  } finally {
    loading.value = false;
  }
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "--";
  }
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: 1,
  }).format(value);
}

function formatTime(value) {
  if (!value) {
    return "--";
  }
  return new Intl.DateTimeFormat(locale.value === "en" ? "en-US" : "zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function priorityClass(level) {
  return {
    critical: "priority-critical",
    high: "priority-high",
    medium: "priority-medium",
    low: "priority-low",
  }[level] || "priority-low";
}

function priorityLabel(row) {
  return t(`common.priority.${row.priority_level || "low"}`);
}

function statusLabel(row) {
  return row.status === "pending"
    ? t("common.status.pending")
    : row.status;
}

function actionText(row) {
  return t("dispatch.action", {
    quantity: row.recommended_quantity,
    source: row.from_station_name,
    target: row.to_station_name,
    deadline: formatTime(row.dispatch_deadline),
  });
}

function reasonText(row) {
  if (row.near_term_demand === null || row.near_term_demand === undefined) {
    return row.reason;
  }
  return t("dispatch.reason", {
    demand: Math.round(row.near_term_demand),
    available: row.current_available_bikes ?? 0,
    target: row.target_bikes ?? 0,
  });
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
      <p class="eyebrow">{{ t("dispatch.eyebrow") }}</p>
      <h1>{{ t("dispatch.title") }}</h1>
      <p class="supporting">{{ t("dispatch.subtitle") }}</p>
    </div>
    <button class="icon-button" type="button" :disabled="loading" @click="loadData">
      <RefreshCw :size="17" :class="{ spinning: loading }" />
      <span>{{ t("common.refresh") }}</span>
    </button>
  </section>

  <div v-if="error" class="alert alert-error">{{ error }}</div>
  <div v-if="summary && !summary.is_current" class="alert alert-warning">
    {{ t("dispatch.stale") }}
  </div>
  <div class="alert alert-info">
    {{ t("dispatch.scope") }}
  </div>

  <section class="metric-grid">
    <article class="metric-card">
      <span class="metric-label">{{ t("dispatch.metric.intervention") }}</span>
      <strong>{{ summary?.deficit_station_count ?? "--" }}</strong>
      <span>
        {{ formatTime(summary?.decision_window_start) }} {{ t("common.to") }}
        {{ formatTime(summary?.decision_window_end) }}
      </span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("dispatch.metric.risk") }}</span>
      <strong>{{ formatNumber(summary?.total_shortage_before) }}</strong>
      <span>{{ t("dispatch.metric.riskHelp") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("dispatch.metric.moves") }}</span>
      <strong>{{ formatNumber(summary?.total_quantity_recommended) }}</strong>
      <span>
        {{
          t("dispatch.metric.movesHelp", {
            count: summary?.recommendation_count ?? 0,
            sources: summary?.source_station_count ?? 0,
          })
        }}
      </span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("dispatch.metric.reduction") }}</span>
      <strong>{{ summary?.shortage_reduction_pct ?? "--" }}%</strong>
      <span>
        {{
          t("dispatch.metric.reductionHelp", {
            count: summary?.estimated_risk_orders_avoided ?? 0,
            pct: summary?.near_term_order_coverage_pct ?? 0,
          })
        }}
      </span>
    </article>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("dispatch.queue.title") }}</h2>
        <p>{{ t("dispatch.queue.subtitle") }}</p>
      </div>
      <span class="panel-tag">{{ t("dispatch.queue.sorted") }}</span>
    </div>
    <div class="action-list">
      <article
        v-for="row in priorityRecommendations"
        :key="`priority-${row.recommendation_id}`"
        class="action-card"
      >
        <div class="action-card-head">
          <span class="priority-badge" :class="priorityClass(row.priority_level)">
            {{
              t("dispatch.priorityBadge", {
                label: priorityLabel(row),
              })
            }}
          </span>
          <span>{{ statusLabel(row) }}</span>
        </div>
        <strong>{{ actionText(row) }}</strong>
        <p>{{ reasonText(row) }}</p>
        <div class="action-facts">
          <span>
            {{
              t("dispatch.queue.distance", {
                distance: formatNumber(row.distance_km),
              })
            }}
          </span>
          <span>
            {{
              t("dispatch.queue.shortage", {
                before: row.shortage_before,
                after: row.shortage_after,
              })
            }}
          </span>
          <span>
            {{
              t("dispatch.queue.lead", {
                minutes: row.lead_time_minutes,
              })
            }}
          </span>
        </div>
      </article>
    </div>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("dispatch.chart.title") }}</h2>
        <p>{{ t("dispatch.chart.subtitle") }}</p>
      </div>
    </div>
    <EChart :option="dispatchOption" height="430px" />
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("dispatch.table.title") }}</h2>
        <p>{{ t("dispatch.table.subtitle") }}</p>
      </div>
      <span class="panel-tag">
        {{
          t("dispatch.table.count", {
            count: recommendations.length,
          })
        }}
      </span>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t("dispatch.table.priority") }}</th>
            <th>{{ t("dispatch.table.from") }}</th>
            <th>{{ t("dispatch.table.to") }}</th>
            <th>{{ t("dispatch.table.quantity") }}</th>
            <th>{{ t("dispatch.table.target") }}</th>
            <th>{{ t("dispatch.table.before") }}</th>
            <th>{{ t("dispatch.table.after") }}</th>
            <th>{{ t("dispatch.table.distance") }}</th>
            <th>{{ t("dispatch.table.deadline") }}</th>
            <th>{{ t("dispatch.table.reason") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in recommendations" :key="row.recommendation_id">
            <td>
              <span
                class="priority-badge"
                :class="priorityClass(row.priority_level)"
              >
                {{ priorityLabel(row) }}
              </span>
            </td>
            <td>
              {{ row.from_station_name }}<br />
              <small>{{ row.from_station_id }}</small>
            </td>
            <td>
              {{ row.to_station_name }}<br />
              <small>{{ row.to_station_id }}</small>
            </td>
            <td>{{ row.recommended_quantity }}</td>
            <td>{{ row.target_bikes ?? "--" }}</td>
            <td>{{ row.shortage_before }}</td>
            <td>{{ row.shortage_after }}</td>
            <td>{{ formatNumber(row.distance_km) }} km</td>
            <td>{{ formatTime(row.dispatch_deadline) }}</td>
            <td>{{ reasonText(row) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
