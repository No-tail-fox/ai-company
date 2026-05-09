<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { ChevronRight, Lock, Sparkles } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import { filterAssistantCardsByCategory, type AssistantCard, type AssistantCenter, type PromptTemplate } from '../services/viewModel';

const props = defineProps<{
  center: AssistantCenter;
}>();

const emit = defineEmits<{
  openAssistant: [assistant: AssistantCard];
  openTemplate: [template: PromptTemplate];
}>();

const activeCategory = ref('全部');
const visibleCategories = computed(() => props.center.categories.slice(0, 8));
const featuredAssistants = computed(() => props.center.featured.slice(0, 4));
const recommendedAssistants = computed(() => filterAssistantCardsByCategory(props.center.assistants, activeCategory.value));
const rankingAssistants = computed(() => props.center.ranking.slice(0, 10));

watch(
  () => props.center.categories,
  (categories) => {
    if (!categories.includes(activeCategory.value)) {
      activeCategory.value = categories[0] ?? '全部';
    }
  }
);
</script>

<template>
  <section class="assistant-page">
    <div class="assistant-layout">
      <div class="assistant-main">
        <header class="assistant-head">
          <div>
            <span class="page-kicker">AI 助理</span>
            <h1>智能助理广场</h1>
            <p>精选优质 AI 助理，覆盖办公、营销、学习、法务等多场景，助你高效解决问题</p>
          </div>
          <button class="assistant-create"><Sparkles :size="18" />一键创建我的助理</button>
        </header>

        <section class="assistant-featured">
          <button v-for="assistant in featuredAssistants" :key="assistant.id" class="featured-assistant" @click="emit('openAssistant', assistant)">
            <span class="assistant-icon"><component :is="getIcon(assistant.icon)" :size="34" /></span>
            <strong>{{ assistant.name }}</strong>
            <p>{{ assistant.description }}</p>
            <small>立即使用</small>
          </button>
        </section>

        <section class="assistant-section">
          <div class="section-title compact">
            <h2>助理分类</h2>
          </div>
          <div class="assistant-categories">
            <button
              v-for="category in visibleCategories"
              :key="category"
              :class="{ active: activeCategory === category }"
              @click="activeCategory = category"
            >
              {{ category }}
            </button>
            <button v-if="center.categories.length > visibleCategories.length" class="more-category">更多<ChevronRight :size="15" /></button>
          </div>
        </section>

        <section class="assistant-section">
          <div class="section-title compact">
            <h2>助理推荐</h2>
          </div>
          <div class="assistant-card-grid">
            <button
              v-for="assistant in recommendedAssistants"
              :key="assistant.id"
              class="assistant-card"
              @click="emit('openAssistant', assistant)"
            >
              <span class="assistant-icon soft"><component :is="getIcon(assistant.icon)" :size="28" /></span>
              <div>
                <strong>{{ assistant.name }}</strong>
                <p>{{ assistant.description }}</p>
                <span class="assistant-meta">
                  <em>{{ assistant.category }}</em>
                  <small>{{ assistant.usageCountLabel }}</small>
                </span>
              </div>
              <Lock v-if="assistant.requiredMembership" :size="15" class="assistant-lock" />
            </button>
          </div>
        </section>
      </div>

      <aside class="assistant-side">
        <section class="assistant-side-box">
          <header>
            <strong>热门助理榜</strong>
            <span>更多</span>
          </header>
          <ol class="assistant-rank-list">
            <li v-for="(assistant, index) in rankingAssistants" :key="assistant.id" @click="emit('openAssistant', assistant)">
              <span>{{ index + 1 }}</span>
              <component :is="getIcon(assistant.icon)" :size="22" />
              <strong>{{ assistant.name }}</strong>
              <em>{{ assistant.usageCountLabel }}</em>
            </li>
          </ol>
        </section>

        <section class="assistant-side-box">
          <header>
            <strong>提示词模板</strong>
            <span>更多</span>
          </header>
          <button v-for="template in center.promptTemplates" :key="template.id" class="prompt-template-row" @click="emit('openTemplate', template)">
            <span class="template-icon"><component :is="getIcon('FileText')" :size="18" /></span>
            <strong>{{ template.title }}</strong>
            <ChevronRight :size="16" />
          </button>
        </section>
      </aside>
    </div>
  </section>
</template>
