<script setup lang="ts">
import { computed } from 'vue';
import { ArrowUpRight, ChevronDown, ChevronRight, PlayCircle, Sparkles, TrendingUp } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import { buildMarketingDashboardModel, type PortalItem, type PortalPageConfig } from '../services/viewModel';

const props = defineProps<{
  pageConfig: PortalPageConfig;
}>();

const emit = defineEmits<{
  openItem: [item: PortalItem];
}>();

const dashboard = computed(() => buildMarketingDashboardModel(props.pageConfig));
const primaryTool = computed(() => dashboard.value.tools[0]);
const sideMetrics = computed(() => dashboard.value.metrics.slice(1, 5));
const channelRows = computed(() =>
  dashboard.value.ranking.slice(0, 5).map((item) => ({
    id: item.id,
    name: item.title,
    icon: item.icon,
    exposure: item.subtitle,
    conversion: item.badge || item.category
  }))
);

function openItem(item?: PortalItem) {
  if (item) {
    emit('openItem', item);
  }
}
</script>

<template>
  <section class="marketing-page">
    <div class="marketing-layout">
      <div class="marketing-main">
        <header class="marketing-head">
          <div>
            <span class="page-kicker">{{ dashboard.page.label }}</span>
            <h1>{{ dashboard.page.title }}</h1>
            <p>{{ dashboard.page.subtitle }}</p>
          </div>
          <button class="marketing-guide" @click="openItem(primaryTool)">
            <PlayCircle :size="18" />
            营销玩法指南
          </button>
        </header>

        <section class="marketing-kpi-panel">
          <div class="marketing-metrics">
            <article v-for="metric in dashboard.metrics" :key="metric.label" class="marketing-metric">
              <span class="marketing-metric-icon"><component :is="getIcon(metric.icon)" :size="18" /></span>
              <small>{{ metric.label }}</small>
              <strong>{{ metric.value }}</strong>
              <em>{{ metric.trend }}</em>
            </article>
          </div>
          <aside class="marketing-boost">
            <div>
              <span>AI 营销加速计划</span>
              <strong>智能洞察 + 精准触达</strong>
              <button @click="openItem(primaryTool)">立即开启</button>
            </div>
            <ArrowUpRight :size="92" />
          </aside>
        </section>

        <section class="marketing-card-section">
          <header class="marketing-section-title">
            <div>
              <h2>营销工具矩阵</h2>
              <p>覆盖全链路营销场景，AI 助你高效产出</p>
            </div>
          </header>
          <div class="marketing-tools-grid">
            <button v-for="tool in dashboard.tools" :key="tool.id" class="marketing-tool-card" @click="openItem(tool)">
              <span class="marketing-tool-icon"><component :is="getIcon(tool.icon)" :size="28" /></span>
              <span class="marketing-tool-copy">
                <strong>{{ tool.title }}</strong>
                <small>{{ tool.subtitle }}</small>
              </span>
              <em>立即生成</em>
            </button>
          </div>
        </section>

        <section class="marketing-card-section">
          <header class="marketing-section-title">
            <div>
              <h2>爆款模板推荐</h2>
              <p>从活动、品牌到案例，快速复用成熟营销资产</p>
            </div>
            <button class="marketing-more">
              更多模板
              <ChevronRight :size="16" />
            </button>
          </header>
          <div class="marketing-template-grid">
            <button
              v-for="template in dashboard.templates"
              :key="template.id"
              class="marketing-template-card"
              @click="openItem(template)"
            >
              <span class="marketing-template-cover">
                <component :is="getIcon(template.icon)" :size="32" />
                <strong>{{ template.title }}</strong>
              </span>
              <span class="marketing-template-copy">
                <strong>{{ template.title }}</strong>
                <small>{{ template.subtitle }}</small>
                <em><Sparkles :size="12" />{{ template.category }}</em>
              </span>
            </button>
          </div>
        </section>
      </div>

      <aside class="marketing-side">
        <section class="marketing-side-card">
          <header>
            <strong>营销数据总览</strong>
            <button>
              近7天
              <ChevronDown :size="15" />
            </button>
          </header>
          <div class="marketing-data-grid">
            <article v-for="metric in sideMetrics" :key="metric.label">
              <small>{{ metric.label }}</small>
              <strong>{{ metric.value }}</strong>
              <em>{{ metric.trend }}</em>
            </article>
          </div>
        </section>

        <section class="marketing-side-card">
          <header>
            <strong>渠道效果排行</strong>
            <button>
              更多
              <ChevronRight :size="15" />
            </button>
          </header>
          <ol class="marketing-channel-list">
            <li v-for="(row, index) in channelRows" :key="row.id">
              <b>{{ index + 1 }}</b>
              <span class="marketing-channel-icon"><component :is="getIcon(row.icon)" :size="18" /></span>
              <strong>{{ row.name }}</strong>
              <small>{{ row.exposure }}</small>
              <em>{{ row.conversion }}</em>
            </li>
          </ol>
        </section>

        <section class="marketing-side-card">
          <header>
            <strong>最近生成记录</strong>
            <button>
              更多
              <ChevronRight :size="15" />
            </button>
          </header>
          <ul class="marketing-record-list">
            <li v-for="record in dashboard.recentRecords" :key="record.title">
              <span>
                <TrendingUp :size="15" />
                {{ record.title }}
              </span>
              <time>{{ record.time }}</time>
            </li>
          </ul>
        </section>
      </aside>
    </div>
  </section>
</template>
