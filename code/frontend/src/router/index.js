import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("../views/HomeView.vue"),
    },
    {
      path: "/forecast",
      name: "forecast",
      component: () => import("../views/ForecastView.vue"),
    },
    {
      path: "/models",
      name: "models",
      component: () => import("../views/ModelsView.vue"),
    },
    {
      path: "/dispatch",
      name: "dispatch",
      component: () => import("../views/DispatchView.vue"),
    },
  ],
});

export default router;
