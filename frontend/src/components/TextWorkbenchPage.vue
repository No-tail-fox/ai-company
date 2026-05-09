<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { getIcon } from '../services/icons';
import type { PortalPageConfig } from '../services/viewModel';

interface WorkbenchAction {
  title: string;
  subtitle: string;
  icon: string;
  prompt: string;
}

interface WorkbenchTemplate {
  title: string;
  category: string;
  tag: string;
  prompt: string;
}

interface WorkbenchRow {
  name: string;
  type: string;
  scene: string;
  metric: string;
  updatedAt: string;
  status: string;
}

interface WorkbenchQueueItem {
  title: string;
  meta: string;
  icon: string;
  progress: number;
  tone: 'processing' | 'pending' | 'success';
}

interface WorkbenchTip {
  title: string;
  text: string;
  icon: string;
}

interface WorkbenchModel {
  key: 'coding' | 'writing';
  title: string;
  subtitle: string;
  cta: string;
  primaryIcon: string;
  primaryTitle: string;
  primarySubtitle: string;
  defaultPrompt: string;
  optionsTitle: string;
  options: string[];
  actions: WorkbenchAction[];
  templateTitle: string;
  templateTabs: string[];
  templates: WorkbenchTemplate[];
  recentTitle: string;
  tableColumns: [string, string, string, string, string, string, string];
  rows: WorkbenchRow[];
  queueTitle: string;
  queueItems: WorkbenchQueueItem[];
  vipTitle: string;
  vipText: string;
  tips: WorkbenchTip[];
}

const props = defineProps<{
  pageConfig: PortalPageConfig;
}>();

const promptText = ref('');

const codingModel: WorkbenchModel = {
  key: 'coding',
  title: 'AI编程工作台',
  subtitle: '代码生成、审查、测试、脚本和项目交付一站式处理',
  cta: '新建代码任务',
  primaryIcon: 'Workflow',
  primaryTitle: '一句话生成代码',
  primarySubtitle: '输入需求、技术栈与边界条件，自动拆解为代码、说明和测试建议。',
  defaultPrompt: '帮我生成一个 Vue3 + TypeScript 的客户列表页面，包含筛选、分页、批量操作和空状态。',
  optionsTitle: '场景',
  options: ['前端组件', '后端接口', '数据脚本', '代码审查', '自动测试'],
  actions: [
    { title: '代码生成', subtitle: '页面、接口与工具函数快速出稿', icon: 'Workflow', prompt: '生成一个可复用的权限按钮组件，支持角色校验、禁用态和加载态。' },
    { title: 'Bug 修复', subtitle: '定位报错并给出最小修改方案', icon: 'ScanSearch', prompt: '分析这段接口请求偶发超时的原因，并给出可落地的修复步骤。' },
    { title: '代码审查', subtitle: '安全、性能和可维护性检查', icon: 'ShieldCheck', prompt: '请按安全、性能、可读性三个维度审查下面的订单导出逻辑。' },
    { title: '单元测试', subtitle: '生成 Vitest、Pytest 测试用例', icon: 'NotebookTabs', prompt: '为用户登录表单生成 Vitest 测试，覆盖校验、提交和错误提示。' },
    { title: '接口文档', subtitle: 'OpenAPI、字段说明和调用示例', icon: 'FileText', prompt: '把订单查询接口整理成 OpenAPI 文档，并补充前端调用示例。' },
    { title: '自动脚本', subtitle: '批处理、爬虫和数据清洗', icon: 'Sparkles', prompt: '写一个 Python 脚本批量整理 CSV 文件，去重、补全字段并输出统计报告。' }
  ],
  templateTitle: '编程模板库',
  templateTabs: ['全部', '前端', '后端', 'Python', '数据库', '测试'],
  templates: [
    { title: '管理后台页面', category: '前端组件', tag: 'Vue', prompt: '生成一个管理后台列表页模板，包含筛选、表格、分页和批量操作。' },
    { title: '登录接口', category: '后端接口', tag: 'API', prompt: '生成登录接口设计，包含参数校验、错误码和鉴权流程。' },
    { title: 'SQL 查询优化', category: '数据库', tag: 'SQL', prompt: '优化一个慢查询 SQL，说明索引建议和执行计划关注点。' },
    { title: '爬虫脚本', category: 'Python', tag: 'PY', prompt: '生成一个带重试、限速和日志的 Python 爬虫脚本。' },
    { title: '测试用例包', category: '自动测试', tag: 'Test', prompt: '为订单模块设计单元测试和边界场景。' },
    { title: '部署脚本', category: 'DevOps', tag: 'CI', prompt: '生成一个前端项目的构建、缓存和发布脚本。' }
  ],
  recentTitle: '最近代码项目',
  tableColumns: ['项目名称', '类型', '技术栈', '进度', '更新时间', '状态', '操作'],
  rows: [
    { name: 'CRM客户列表页', type: '前端组件', scene: 'Vue3', metric: '82%', updatedAt: '2026-05-09 16:20', status: '生成中' },
    { name: '订单查询接口', type: '后端接口', scene: 'FastAPI', metric: '100%', updatedAt: '2026-05-09 14:08', status: '已完成' },
    { name: '权限模块审查', type: '代码审查', scene: 'TypeScript', metric: '100%', updatedAt: '2026-05-08 18:42', status: '已完成' },
    { name: 'CSV 清洗脚本', type: '数据脚本', scene: 'Python', metric: '44%', updatedAt: '2026-05-08 11:35', status: '排队中' }
  ],
  queueTitle: '代码任务队列',
  queueItems: [
    { title: '权限模块重构', meta: '预计 35 秒', icon: 'Workflow', progress: 68, tone: 'processing' },
    { title: '登录表单测试', meta: '排队 2 个', icon: 'NotebookTabs', progress: 22, tone: 'pending' },
    { title: 'SQL 索引建议', meta: '已完成', icon: 'ChartColumn', progress: 100, tone: 'success' },
    { title: '接口文档整理', meta: '排队 4 个', icon: 'FileText', progress: 12, tone: 'pending' }
  ],
  vipTitle: '开通会员，解锁团队级编程特权',
  vipText: '更高并发、长代码上下文、私有模板库和优先队列',
  tips: [
    { title: '先写清输入输出', text: '明确函数签名、数据结构和异常场景，生成结果会更稳。', icon: 'FileText' },
    { title: '把报错原文贴完整', text: '包含堆栈、环境和复现步骤，能更快定位问题。', icon: 'ScanSearch' },
    { title: '代码审查分维度', text: '安全、性能、可读性和测试覆盖建议分开检查。', icon: 'ShieldCheck' }
  ]
};

const writingModel: WorkbenchModel = {
  key: 'writing',
  title: 'AI写作中心',
  subtitle: '文章、报告、简历、论文和运营内容从提纲到成稿',
  cta: '新建写作项目',
  primaryIcon: 'Feather',
  primaryTitle: '从主题到成稿',
  primarySubtitle: '输入主题、受众和语气，自动生成大纲、正文、标题和润色建议。',
  defaultPrompt: '请帮我写一篇面向中小企业主的 AI 工具趋势文章，语气专业、结构清晰、适合公众号发布。',
  optionsTitle: '体裁',
  options: ['公众号', '小红书', '报告', '论文润色', '简历优化'],
  actions: [
    { title: '文章创作', subtitle: '标题、大纲、正文一键生成', icon: 'Feather', prompt: '围绕“AI 提升团队效率”写一篇 1800 字公众号文章。' },
    { title: '公众号推文', subtitle: '开头钩子、段落和排版建议', icon: 'MessageCircle', prompt: '生成一篇面向创业者的公众号推文，主题是 AI 自动化办公。' },
    { title: '小红书笔记', subtitle: '种草文案、标签和封面标题', icon: 'Megaphone', prompt: '写一篇小红书笔记，介绍 5 个适合新手的 AI 写作技巧。' },
    { title: '报告生成', subtitle: '结构化观点、数据和摘要', icon: 'ChartColumn', prompt: '生成一份 AI 工具市场调研报告大纲，包含摘要、趋势和建议。' },
    { title: '论文润色', subtitle: '逻辑、表达和学术语气优化', icon: 'GraduationCap', prompt: '润色一段论文引言，使逻辑更顺、语气更正式。' },
    { title: '简历优化', subtitle: '经历改写、亮点提炼和匹配岗位', icon: 'UserRound', prompt: '把运营岗位经历改写成更适合 AI 产品运营求职的简历描述。' }
  ],
  templateTitle: '写作模板库',
  templateTabs: ['全部', '自媒体', '商务', '学术', '求职', '营销'],
  templates: [
    { title: '爆款标题库', category: '自媒体', tag: 'Hot', prompt: '为 AI 办公主题生成 20 个公众号标题。' },
    { title: '报告大纲', category: '商务报告', tag: 'DOC', prompt: '生成一份行业分析报告大纲，包含摘要、趋势、案例和建议。' },
    { title: '简历亮点', category: '求职', tag: 'CV', prompt: '提炼项目经历亮点，改写成 STAR 结构。' },
    { title: '品牌故事', category: '营销文案', tag: 'Brand', prompt: '为一家 AI 教育社区写品牌故事和使命表达。' },
    { title: '邮件模板', category: '商务沟通', tag: 'Mail', prompt: '写一封合作邀约邮件，语气专业但不生硬。' },
    { title: '演讲稿', category: '公开表达', tag: 'Talk', prompt: '写一段 3 分钟演讲稿，主题是 AI 时代的个人成长。' }
  ],
  recentTitle: '最近写作项目',
  tableColumns: ['项目名称', '类型', '语气', '字数', '更新时间', '状态', '操作'],
  rows: [
    { name: 'AI工具趋势报告', type: '行业报告', scene: '商务正式', metric: '2840字', updatedAt: '2026-05-09 15:42', status: '润色中' },
    { name: '新手入门公众号', type: '公众号', scene: '清晰友好', metric: '1820字', updatedAt: '2026-05-09 13:18', status: '已完成' },
    { name: '产品经理简历', type: '简历优化', scene: '专业简洁', metric: '980字', updatedAt: '2026-05-08 17:50', status: '已完成' },
    { name: '社群招募文案', type: '营销文案', scene: '有号召力', metric: '620字', updatedAt: '2026-05-08 10:25', status: '排队中' }
  ],
  queueTitle: '写作任务队列',
  queueItems: [
    { title: 'AI工具趋势报告', meta: '润色中', icon: 'ChartColumn', progress: 74, tone: 'processing' },
    { title: '公众号标题组', meta: '排队 1 个', icon: 'MessageCircle', progress: 28, tone: 'pending' },
    { title: '简历项目改写', meta: '已完成', icon: 'UserRound', progress: 100, tone: 'success' },
    { title: '社群招募文案', meta: '排队 3 个', icon: 'Megaphone', progress: 14, tone: 'pending' }
  ],
  vipTitle: '开通会员，解锁高阶写作权益',
  vipText: '长文续写、批量改写、专属语气库和商业模板',
  tips: [
    { title: '先定义读者', text: '说明读者身份、阅读场景和期望行动，文章会更聚焦。', icon: 'Users' },
    { title: '给出语气样例', text: '贴一段喜欢的表达风格，可快速稳定输出调性。', icon: 'Feather' },
    { title: '分轮次打磨', text: '先定结构，再补事实，最后统一标题和金句。', icon: 'Sparkles' }
  ]
};

const pageModel = computed(() => (props.pageConfig.page.pageKey === 'writing' ? writingModel : codingModel));

watch(
  pageModel,
  (model) => {
    promptText.value = model.defaultPrompt;
  },
  { immediate: true }
);

function useAction(action: WorkbenchAction) {
  promptText.value = action.prompt;
}

function useTemplate(template: WorkbenchTemplate) {
  promptText.value = template.prompt;
}
</script>

<template>
  <section :class="['craft-page', `${pageModel.key}-mode`]">
    <div class="craft-layout">
      <div class="craft-main">
        <header class="craft-head">
          <div>
            <h1>{{ pageModel.title }}</h1>
            <p>{{ pageModel.subtitle }}</p>
          </div>
          <button class="craft-create-btn">
            <component :is="getIcon(pageModel.primaryIcon)" :size="18" />
            {{ pageModel.cta }}
          </button>
        </header>

        <section class="craft-hero-grid">
          <article class="craft-primary-tool">
            <div class="craft-tool-copy">
              <h2>{{ pageModel.primaryTitle }}</h2>
              <p>{{ pageModel.primarySubtitle }}</p>
              <textarea v-model="promptText" rows="4" />
              <div class="craft-option-row">
                <span>{{ pageModel.optionsTitle }}</span>
                <button v-for="option in pageModel.options" :key="option" :class="{ active: option === pageModel.options[0] }">
                  {{ option }}
                </button>
              </div>
              <button class="craft-submit">
                立即生成
                <component :is="getIcon('Sparkles')" :size="17" />
              </button>
            </div>

            <div class="craft-preview-card" aria-hidden="true">
              <div class="craft-preview-window">
                <span></span><span></span><span></span>
              </div>
              <div v-if="pageModel.key === 'coding'" class="code-preview">
                <div class="code-sidebar"></div>
                <div class="code-lines">
                  <span><b>const</b> page = buildTable();</span>
                  <span><b>await</b> fetchCustomers(filters);</span>
                  <span><b>return</b> &lt;DataGrid /&gt;;</span>
                  <span><b>test</b>('renders empty state');</span>
                </div>
                <div class="terminal-preview">
                  <strong>task: code</strong>
                  <small>82% generating</small>
                </div>
              </div>
              <div v-else class="writing-preview">
                <div class="doc-sheet">
                  <strong>AI 工具趋势报告</strong>
                  <span></span><span></span><span></span>
                  <em>摘要</em>
                  <span class="wide"></span><span class="short"></span>
                </div>
                <div class="outline-stack">
                  <i></i><i></i><i></i>
                </div>
              </div>
            </div>
          </article>

          <button v-for="action in pageModel.actions" :key="action.title" class="craft-action-card" @click="useAction(action)">
            <span><component :is="getIcon(action.icon)" :size="28" /></span>
            <strong>{{ action.title }}</strong>
            <p>{{ action.subtitle }}</p>
          </button>
        </section>

        <section class="craft-panel">
          <div class="craft-section-title">
            <div>
              <h2>{{ pageModel.templateTitle }}</h2>
              <nav>
                <span v-for="tab in pageModel.templateTabs" :key="tab">{{ tab }}</span>
              </nav>
            </div>
            <button>更多模板 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="craft-template-strip">
            <button v-for="template in pageModel.templates" :key="template.title" class="craft-template" @click="useTemplate(template)">
              <strong>{{ template.title }}</strong>
              <small>{{ template.category }}</small>
              <em>{{ template.tag }}</em>
            </button>
          </div>
        </section>

        <section class="craft-panel">
          <div class="craft-section-title compact">
            <h2>{{ pageModel.recentTitle }}</h2>
            <button>查看全部项目 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="craft-table">
            <div class="craft-row craft-row-head">
              <span v-for="column in pageModel.tableColumns" :key="column">{{ column }}</span>
            </div>
            <div v-for="row in pageModel.rows" :key="row.name" class="craft-row">
              <strong>{{ row.name }}</strong>
              <span>{{ row.type }}</span>
              <span>{{ row.scene }}</span>
              <span>{{ row.metric }}</span>
              <span>{{ row.updatedAt }}</span>
              <span :class="['craft-status', row.status === '已完成' ? 'success' : row.status === '排队中' ? 'pending' : 'processing']">
                {{ row.status }}
              </span>
              <span class="craft-actions">下载 打开</span>
            </div>
          </div>
        </section>
      </div>

      <aside class="craft-side">
        <section class="craft-side-box">
          <header>
            <strong>{{ pageModel.queueTitle }}</strong>
            <span>全部任务</span>
          </header>
          <div class="craft-queue-list">
            <article v-for="item in pageModel.queueItems" :key="item.title">
              <span><component :is="getIcon(item.icon)" :size="22" /></span>
              <div>
                <strong>{{ item.title }}</strong>
                <i><b :class="item.tone" :style="{ width: `${item.progress}%` }"></b></i>
                <small>{{ item.meta }}</small>
              </div>
              <em>{{ item.progress }}%</em>
            </article>
          </div>
        </section>

        <section class="craft-vip-panel">
          <div>
            <strong>{{ pageModel.vipTitle }}</strong>
            <span>{{ pageModel.vipText }}</span>
          </div>
          <button>开通会员</button>
        </section>

        <section class="craft-side-box">
          <header>
            <strong>创作小贴士</strong>
            <span>更多</span>
          </header>
          <button v-for="tip in pageModel.tips" :key="tip.title" class="craft-tip">
            <component :is="getIcon(tip.icon)" :size="21" />
            <span>
              <strong>{{ tip.title }}</strong>
              <small>{{ tip.text }}</small>
            </span>
          </button>
        </section>
      </aside>
    </div>
  </section>
</template>
