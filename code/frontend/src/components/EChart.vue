<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  height: {
    type: String,
    default: "320px",
  },
});

const chartElement = ref(null);
let chart;
let resizeObserver;

function renderChart() {
  if (!chart) {
    return;
  }
  chart.setOption(props.option, true);
}

onMounted(() => {
  chart = echarts.init(chartElement.value);
  renderChart();
  resizeObserver = new ResizeObserver(() => chart?.resize());
  resizeObserver.observe(chartElement.value);
});

watch(
  () => props.option,
  () => renderChart(),
  { deep: true },
);

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <div ref="chartElement" class="chart-host" :style="{ height }" />
</template>
