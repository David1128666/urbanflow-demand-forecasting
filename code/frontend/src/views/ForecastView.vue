<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import {
  getDemandHistory,
  getLatestInventory,
  getLatestForecasts,
  getStations,
} from "../api";
import EChart from "../components/EChart.vue";
import { locale, t } from "../i18n";

const stations = ref([]);
const selectedStation = ref("");
const history = ref([]);
const forecast = ref([]);
const inventory = ref(null);
const operation = ref(null);
const run = ref({});
const loading = ref(false);
const error = ref("");
let refreshTimer;

const summary = computed(() => {
  const values = forecast.value.map((row) => Number(row.predicted_demand));
  if (!values.length) {
    return { total: 0, mean: 0, peak: 0 };
  }
  return {
    total: values.reduce((sum, value) => sum + value, 0),
    mean: values.reduce((sum, value) => sum + value, 0) / values.length,
    peak: Math.max(...values),
  };
});

const selectedStationLabel = computed(() => {
  const station = stations.value.find(
    (item) => item.station_id === selectedStation.value,
  );
  return station
    ? `${station.station_id} · ${station.station_name}`
    : selectedStation.value;
});

const operationStatus = computed(() => {
  if (!operation.value) {
    return "--";
  }
  const replenishment = Number(
    operation.value.recommended_replenishment || 0,
  );
  const available = Number(operation.value.current_available_bikes || 0);
  const docks = Number(operation.value.current_available_docks || 0);
  if (replenishment > 0 && available <= 5) {
    return t("forecast.status.urgent");
  }
  if (replenishment > 0) {
    return t("forecast.status.replenish");
  }
  if (operation.value.station_status === "full" || docks <= 3) {
    return t("forecast.status.returnPressure");
  }
  return t("forecast.status.normal");
});

const stationStatus = computed(() => {
  const status = operation.value?.station_status;
  return status
    ? t(`forecast.stationStatus.${status}`)
    : "--";
});

const recommendedAction = computed(() => {
  if (!operation.value) {
    return t("forecast.operation.noAction");
  }
  const available = operation.value.current_available_bikes;
  if (available === null || available === undefined) {
    return t("forecast.action.noInventory");
  }
  const replenishment = Number(
    operation.value.recommended_replenishment || 0,
  );
  if (replenishment > 0) {
    return t("forecast.action.replenish", {
      demand: Math.round(operation.value.next_2h_orders || 0),
      available,
      target: operation.value.target_bikes,
      quantity: replenishment,
      deadline: formatTime(operation.value.decision_deadline),
    });
  }
  if (
    operation.value.station_status === "full" ||
    Number(operation.value.current_available_docks || 0) <= 3
  ) {
    return t("forecast.action.returnPressure", {
      available,
      docks: operation.value.current_available_docks,
    });
  }
  return t("forecast.action.normal", {
    available,
    target: operation.value.target_bikes,
  });
});

const forecastOption = computed(() => {
  const historyRows = history.value;
  const forecastRows = forecast.value;
  const labels = [
    ...historyRows.map((row) => row.window_start),
    ...forecastRows.map((row) => row.target_time),
  ];
  const historySeries = [
    ...historyRows.map((row) => Number(row.demand_count)),
    ...forecastRows.map(() => null),
  ];
  const forecastSeries = [
    ...historyRows.slice(0, -1).map(() => null),
    historyRows.length
      ? Number(historyRows[historyRows.length - 1].demand_count)
      : null,
    ...forecastRows.map((row) => Number(row.predicted_demand)),
  ];

  return {
    animationDuration: 450,
    grid: { left: 54, right: 24, top: 44, bottom: 72 },
    tooltip: { trigger: "axis" },
    legend: {
      top: 4,
      data: ["history", "forecast"].map((key) =>
        t(`forecast.chart.${key}`),
      ),
      textStyle: { color: "#53626f" },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: labels,
      axisLabel: {
        color: "#667582",
        formatter: (value) => formatChartTime(value),
      },
      axisLine: { lineStyle: { color: "#cfd8df" } },
    },
    yAxis: {
      type: "value",
      name: t("forecast.chart.yAxis"),
      splitLine: { lineStyle: { color: "#e8edf1" } },
    },
    series: [
      {
        name: t("forecast.chart.history"),
        type: "line",
        data: historySeries,
        showSymbol: false,
        smooth: true,
        lineStyle: { color: "#2b6f71", width: 2.2 },
        itemStyle: { color: "#2b6f71" },
      },
      {
        name: t("forecast.chart.forecast"),
        type: "line",
        data: forecastSeries,
        showSymbol: false,
        smooth: true,
        lineStyle: { color: "#df8b25", width: 2.6 },
        itemStyle: { color: "#df8b25" },
        areaStyle: { color: "rgba(223, 139, 37, 0.10)" },
      },
    ],
  };
});

async function loadStations() {
  loading.value = true;
  error.value = "";
  try {
    stations.value = await getStations({ limit: 500 });
    if (stations.value.length) {
      selectedStation.value = stations.value[0].station_id;
      await loadStation();
    }
  } catch (requestError) {
    error.value = requestError.message || t("forecast.error.stations");
  } finally {
    loading.value = false;
  }
}

async function loadStation() {
  if (!selectedStation.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const [historyPayload, forecastPayload, inventoryPayload] = await Promise.all([
      getDemandHistory({
        station_id: selectedStation.value,
        limit: 192,
      }),
      getLatestForecasts({
        station_id: selectedStation.value,
        limit: 48,
      }),
      getLatestInventory({
        station_id: selectedStation.value,
      }),
    ]);
    history.value = historyPayload.points;
    forecast.value = forecastPayload.points;
    operation.value = forecastPayload.operation_summary;
    run.value = forecastPayload.run || {};
    inventory.value = inventoryPayload[0] || null;
  } catch (requestError) {
    error.value = requestError.message || t("forecast.error.data");
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

function formatChartTime(value) {
  return formatTime(value).replace("/", "-");
}

function demandImpact(point) {
  const value = Number(point.predicted_demand);
  if (value >= 25) {
    return t("forecast.impact.veryHigh");
  }
  if (value >= 15) {
    return t("forecast.impact.high");
  }
  if (value >= 6) {
    return t("forecast.impact.normal");
  }
  return t("forecast.impact.low");
}

onMounted(async () => {
  await loadStations();
  refreshTimer = window.setInterval(loadStation, 10000);
});

onBeforeUnmount(() => {
  window.clearInterval(refreshTimer);
});
</script>

<template>
  <section class="page-heading">
    <div>
      <p class="eyebrow">{{ t("forecast.eyebrow") }}</p>
      <h1>{{ t("forecast.title") }}</h1>
      <p class="supporting">{{ t("forecast.subtitle") }}</p>
    </div>
    <div class="heading-actions">
      <select v-model="selectedStation" class="select-control" @change="loadStation">
        <option v-for="station in stations" :key="station.station_id" :value="station.station_id">
          {{ station.station_id }} · {{ station.station_name }}
        </option>
      </select>
      <button class="icon-button" type="button" :disabled="loading" @click="loadStation">
        <RefreshCw :size="17" :class="{ spinning: loading }" />
        <span>{{ t("common.refresh") }}</span>
      </button>
    </div>
  </section>

  <div v-if="error" class="alert alert-error">{{ error }}</div>

  <section class="metric-grid">
    <article class="metric-card">
      <span class="metric-label">{{ t("forecast.metric.nextTwoHours") }}</span>
      <strong>{{ formatNumber(operation?.next_2h_orders ?? 0) }}</strong>
      <span>{{ t("forecast.metric.nextTwoHoursHelp") }}</span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("forecast.metric.available") }}</span>
      <strong>{{ formatNumber(operation?.current_available_bikes) }}</strong>
      <span>
        {{
          t("forecast.metric.snapshot", {
            time: formatTime(operation?.snapshot_time),
            capacity: inventory?.capacity ?? "--",
          })
        }}
      </span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("forecast.metric.replenishment") }}</span>
      <strong>{{ formatNumber(operation?.recommended_replenishment) }}</strong>
      <span>
        {{
          t("forecast.metric.target", {
            target: operation?.target_bikes ?? "--",
            safety: operation?.safety_stock ?? "--",
          })
        }}
      </span>
    </article>
    <article class="metric-card">
      <span class="metric-label">{{ t("forecast.metric.operationStatus") }}</span>
      <strong>{{ operationStatus }}</strong>
      <span>
        {{
          t("forecast.metric.deadline", {
            time: formatTime(operation?.decision_deadline),
          })
        }}
      </span>
    </article>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>
          {{ t("forecast.chart.title", { station: selectedStationLabel }) }}
        </h2>
        <p>
          {{
            t("forecast.chart.subtitle", {
              cutoff: formatTime(run.data_cutoff),
              start: formatTime(forecast[0]?.target_time),
            })
          }}
        </p>
      </div>
    </div>
    <EChart :option="forecastOption" height="430px" />
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("forecast.operation.title") }}</h2>
        <p>{{ t("forecast.operation.subtitle") }}</p>
      </div>
      <span class="panel-tag">{{ run.model_version || "--" }}</span>
    </div>
    <div class="detail-grid">
      <div>
        <span class="detail-label">{{ t("forecast.operation.available") }}</span>
        <strong>{{ operation?.current_available_bikes ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("forecast.operation.docks") }}</span>
        <strong>{{ operation?.current_available_docks ?? "--" }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("forecast.operation.stationStatus") }}</span>
        <strong>{{ stationStatus }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("forecast.operation.peak") }}</span>
        <strong>{{ formatNumber(operation?.peak_window_orders) }}</strong>
      </div>
      <div>
        <span class="detail-label">{{ t("forecast.operation.run") }}</span>
        <strong>{{ run.forecast_run_id ?? "--" }}</strong>
      </div>
    </div>
    <div class="action-callout">
      <span>{{ t("forecast.operation.action") }}</span>
      <strong>{{ recommendedAction }}</strong>
    </div>
  </section>

  <section class="panel">
    <div class="panel-heading">
      <div>
        <h2>{{ t("forecast.points.title") }}</h2>
        <p>{{ t("forecast.points.subtitle") }}</p>
      </div>
      <span class="panel-tag">
        {{ t("forecast.points.count", { count: forecast.length }) }}
      </span>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t("forecast.table.window") }}</th>
            <th>{{ t("forecast.table.orders") }}</th>
            <th>{{ t("forecast.table.meaning") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="point in forecast" :key="point.horizon_step">
            <td>
              {{ formatTime(point.window_start) }} {{ t("common.to") }}
              {{ formatTime(point.window_end) }}
            </td>
            <td>{{ formatNumber(point.predicted_demand) }}</td>
            <td>{{ demandImpact(point) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
