import { expect, test } from 'vitest';
import {
  buildAudioTaskPayload,
  createFallbackPageConfig,
  createFallbackAudioWorkbenchPageConfig,
  getAudioSection,
  shouldUseAudioPage,
  type PortalItem,
  type PortalPageConfig
} from '../src/services/viewModel';

test('uses the dedicated audio page only for the audio route', () => {
  expect(shouldUseAudioPage('audio')).toBe(true);
  expect(shouldUseAudioPage('assistant')).toBe(false);
  expect(shouldUseAudioPage('home')).toBe(false);
});

test('fallback audio catalog page keeps generic portal sections', () => {
  const audioPage = createFallbackPageConfig('audio');

  expect(audioPage.sections.map((section) => section.layout)).toEqual(expect.arrayContaining(['stat-strip', 'tool-grid']));
  expect(getAudioSection(audioPage, 'audio-tools')).toBeUndefined();
});

test('audio workbench fallback keeps dedicated workbench sections', () => {
  const workbenchPage = createFallbackAudioWorkbenchPageConfig();

  expect(workbenchPage.page.pageKey).toBe('workbench-audio');
  expect(workbenchPage.sections.map((section) => section.layout)).toEqual(
    expect.arrayContaining([
      'audio-workbench',
      'audio-stats',
      'audio-tools',
      'audio-voices',
      'audio-table',
      'audio-queue',
      'audio-resources',
      'audio-guides'
    ])
  );
  expect(getAudioSection(workbenchPage, 'audio-tools')?.items.length).toBeGreaterThanOrEqual(8);
});

test('finds an audio section by its dedicated layout', () => {
  const pageConfig: PortalPageConfig = {
    tenantId: 'demo',
    page: {
      pageKey: 'audio',
      label: 'AI 音频',
      title: 'AI音频工作台',
      subtitle: '',
      icon: 'Headphones',
      sortOrder: 50,
      enabled: true
    },
    sections: [
      {
        id: 'section-audio-tools',
        pageKey: 'audio',
        sectionKey: 'tools',
        title: '音频工具中心',
        subtitle: '',
        layout: 'audio-tools',
        sortOrder: 10,
        enabled: true,
        items: []
      }
    ]
  };

  expect(getAudioSection(pageConfig, 'audio-tools')?.sectionKey).toBe('tools');
  expect(getAudioSection(pageConfig, 'tool-grid')).toBeUndefined();
});

test('builds audio task payload from selected tool and voice', () => {
  const selectedTool: PortalItem = {
    id: 'audio-tool-1',
    itemType: 'tool',
    title: '文本转语音',
    subtitle: '多音色高拟真配音',
    category: '音频工具',
    icon: 'Headphones',
    sortOrder: 10,
    enabled: true,
    actionType: 'workspace',
    actionValue: 'audio_tts',
    requiredMembership: false,
    pointCost: 120,
    metadata: {}
  };
  const voice: PortalItem = {
    id: 'audio-voice-1',
    itemType: 'voice',
    title: '知性女声',
    subtitle: '温柔 · 知性',
    category: '女声',
    icon: 'CircleUserRound',
    sortOrder: 10,
    enabled: true,
    actionValue: 'voice-warm-female',
    requiredMembership: false,
    pointCost: 0,
    metadata: {}
  };

  expect(buildAudioTaskPayload(selectedTool, '欢迎使用 AI 音频工作台', voice)).toEqual({
    task_type: 'TTS',
    route_key: 'audio_tts',
    prompt: '欢迎使用 AI 音频工作台',
    source_url: '',
    voice_key: 'voice-warm-female',
    target_type: 'builtin',
    target_id: 'audio_tts',
    surface: 'portal'
  });
});

test('builds audio task payloads for the workbench namespace when requested', () => {
  const selectedTool: PortalItem = {
    id: 'audio-tool-1',
    itemType: 'tool',
    title: '文本转语音',
    subtitle: '多音色高拟真配音',
    category: '音频工具',
    icon: 'Headphones',
    sortOrder: 10,
    enabled: true,
    actionType: 'workspace',
    actionValue: 'audio_tts',
    requiredMembership: false,
    pointCost: 120,
    metadata: {}
  };

  expect(buildAudioTaskPayload(selectedTool, '工作台音频任务', undefined, '', 'workbench')).toMatchObject({
    surface: 'workbench',
    route_key: 'audio_tts',
    task_type: 'TTS'
  });
});
