<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import { getModelMetrics } from "../api";
import EChart from "../components/EChart.vue";
import { locale, t } from "../i18n";

const metrics = ref({ selection: null, model_card: null, models: [] });
const loading = ref(false);
const error = ref("");
let refreshTimer;

const selectedModel = computed(
  () => modelName(metrics.value.selection?.selected_model),
);
const modelCard = computed(() => metrics.value.model_card || {});

const activeModelType = computed(() => {
  if (modelCard.value.active_model === "tcn") {
    return t("models.type.tcn");
  }
  if (modelCard.value.active_model === "seasonal_naive") {
    return t("models.type.baseline");
  }
  return "--";
});

const selectionReason = computed(() => {
  const selection = metrics.value.selection;
  if (!selection) {
    return "--";
  }
  const improvement = Math.abs(
    Number(selection.tcn_improvement || 0) * 100,
  ).toFixed(2);
  const required = Number(
    selection.minimum_improvement || 0,
  ) * 100;
  if (selection.selected_model === "tcn") {
    return t("models.reason.tcn", {
      improvement,
      required,
    });
  }
  return t("models.reason.baseline", {
    improvement,
    required,
  });
});

const metricRows = computed(() =>
  metrics.value.models.flatMap((model) => [
    {
      model: model.model,
      version: model.version,
      split: t("common.validation"),
      mae: model.validation?.mae,
      rmse: model.validation?.rmse,
      smape: model.validation?.smape,
    },
    {
      model: model.model,
      version: model.version,
      split: t("common.test"),
      mae: model.test?.mae,
      rmse: model.test?.rmse,
      smape: model.test?.smape,
    },
  ]),
);

const comparisonOption = computed(() => {
  const models = metrics.value.models;
  return {
    grid: { left: 52, right: 24, top: 42, bottom: 44 },
    tooltip: { trigger: "axis" },
    legend: {
      top: 4,
      data: [
        t("models.chart.validationMae"),
        t("models.chart.testMae"),
      ],
    },
    xAxis: {
      type: "category",
      data: models.map((model) =>
        model.model === "tcn" ? "TCN" : "Seasonal Naive",
      ),
      axisLine: { lineStyle: { color: "#cfd8df" } },
    },
    yAxis: {
      type: "value",
      name: "MAE",
      splitLine: { lineStyle: { color: "#e8edf1" } },
    },
    series: [
      {
        name: t("models.chart.validationMae"),
        type: "bar",
        data: models.map((model) => model.validation?.mae),
        itemStyle: { color: "#2b6f71" },
        barWidth: 28,
      },
      {
        name: t("models.chart.testMae"),
        type: "bar",
        data: models.map((model) => model.test?.mae),
        itemStyle: { color: "#e09a2d" },
        barWidth: 28,
      },
    ],
  };
});

async function loadMetrics() {
  loading.value = true;
  error.value = "";
  try {
    metrics.value = await getModelMetrics();
  } catch (requestError) {
    error.value = requestError.message || t("models.error");
  } finally {
    loading.value = false;
  }
}

function formatMetric(value) {
  if (value === null || value === undefined) {
    return "--";
  }
  return Number(value).toFixed(4);
}

function formatTimestamp(value) {
  if (!value) {
    return "--";
  }
  return new Intl.DateTimeFormat(locale.value === "en" ? "en-US" : "zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function modelName(value) {
  if (value === "seasonal_naive") {
    return t("models.name.seasonal");
  }
  if (value === "tcn") {
    return t("models.name.tcn");
  }
  return value || "--";
}

onMounted(() => {
  loadMetrics();
  refreshTimer = window.setInterval(loadMetrics, 60000);
});

onBeforeUnmount(() => {
  window.clearInterval(refreshTimer);
});
</script>

<template>
  <section class="page-heading">
    <div>
      <p class="eyebrow">{{ t("models.eyebrow") }}</p>
      <h1>{{ t("models.title") }}</h1>
      <p class="supporting">{{ t("models.subtitle") }}</p>
    </div>
    <button class="icon-button" type="button" :disabled="loading" @click="loadMetrics">
      <RefreshCw :size="17" :class="{ spinning: loading }" />
      <span>{{ t("common.refresh") }}</span>
    </button>
  </section>

  <div v-if="error" class="alert alert-error">{{ error }}</div>

  <section class="metric-grid">
    <article class="metric-card">
      <span class="metric-label">{{ t("models.current") }}</span>
      <strong>{{ selectedModel }}</strong>
      <span>{{ metrics.selection?.model_version || "--" }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("models.baselineMae") }}</span>
      <strong>{{ formatMetric(metrics.selection?.baseline_mae) }}</strong>
      <span>Seasonal Naive</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("models.tcnMae") }}</span>
      <strong>{{ formatMetric(metrics.selection?.tcn_mae) }}</strong>
      <span>{{ t("models.experimental") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("models.threshold") }}</span>
      <strong>
        {{ ((metrics.selection?.minimum_improvement || 0) * 100).toFixed(0) }}%
      </strong>
      <span>{{ t("models.thresholdHelp") }}</span>
    </article>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("models.card.title") }}</h2>
        <p>{{ t("models.card.subtitle") }}</p>
      </div>
      <span class="panel-tag">{{ modelCard.model_version || "--" }}</span>
    </div>
    <div class="model-card-grid">
      <div>
        <span class="detail-label">{{ t("models.card.modelType") }}</span>
        <strong>{{ activeModelType }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("models.card.selectionRule") }}</span>
        <strong class="model-card-rule">
          {{ t("models.rule") }}
        </strong>
      </div>
      <div>
        <span class="detail-label">{{ t("models.card.improvement") }}</span>
        <strong>
          {{ formatMetric(modelCard.challenger_improvement_pct) }}%
        </strong>
      </div>
      <div>
        <span class="detail-label">
          {{ t("models.card.challengerUpdated") }}
        </span>
        <strong>{{ formatTimestamp(modelCard.challenger_artifact_updated_at) }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("models.card.dataMode") }}</span>
        <strong>{{ t("home.dataMode") }}</strong>
      </div>
    </div>
    <div class="model-card-footer">
      <div>
        <span class="detail-label">{{ t("models.card.limitations") }}</span>
        <ul>
          <li>{{ t("models.limitation.synthetic") }}</li>
          <li>{{ t("models.limitation.intervals") }}</li>
        </ul>
      </div>
      <p>{{ selectionReason }}</p>
    </div>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("models.chart.title") }}</h2>
        <p>{{ t("models.chart.subtitle") }}</p>
      </div>
    </div>
    <EChart :option="comparisonOption" height="360px" />
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("models.table.title") }}</h2>
        <p>{{ t("models.table.subtitle") }}</p>
      </div>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t("models.table.model") }}</th>
            <th>{{ t("models.table.version") }}</th>
            <th>{{ t("models.table.dataset") }}</th>
            <th>MAE</th>
            <th>RMSE</th>
            <th>sMAPE</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in metricRows" :key="`${row.version}-${row.split}`">
            <td>{{ modelName(row.model) }}</td>
            <td>{{ row.version }}</td>
            <td>{{ row.split }}</td>
            <td>{{ formatMetric(row.mae) }}</td>
            <td>{{ formatMetric(row.rmse) }}</td>
            <td>{{ formatMetric(row.smape) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="selection-reason">{{ metrics.selection?.reason }}</p>
  </section>
</template>
