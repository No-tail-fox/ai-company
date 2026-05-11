import { afterEach, expect, test, vi } from 'vitest';
import {
  createImageGeneration,
  createVideoGeneration,
  fetchAudioTasks,
  fetchImageWorkbench,
  fetchVideoWorkbench
} from '../src/services/api';

function mockFetchResponse(payload: any) {
  return {
    ok: true,
    json: async () => payload
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test('image generation request includes target binding fields', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'image-task-1',
      tenant_id: 'demo',
      user_id: 'demo-user',
      task_type: 'IMAGE',
      route_key: 'image_text_to_image',
      prompt: 'demo',
      status: 'PENDING',
      estimated_cost: 45
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await createImageGeneration('生成商品海报', {
    requestKey: 'image-1',
    targetType: 'builtin',
    targetId: 'image_action_poster',
    routeKey: 'legacy-route'
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    prompt: '生成商品海报',
    user_id: 'demo-user',
    route_key: 'legacy-route',
    request_key: 'image-1',
    target_type: 'builtin',
    target_id: 'image_action_poster',
    surface: 'portal'
  });
});

test('video generation request includes target binding fields', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'video-task-1',
      tenant_id: 'demo',
      user_id: 'demo-user',
      task_type: 'VIDEO',
      route_key: 'video_text_to_video',
      prompt: 'demo',
      status: 'PENDING',
      estimated_cost: 200
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await createVideoGeneration('生成新品视频', {
    requestKey: 'video-1',
    targetType: 'builtin',
    targetId: 'video_action_product',
    routeKey: 'legacy-route'
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    prompt: '生成新品视频',
    user_id: 'demo-user',
    route_key: 'legacy-route',
    request_key: 'video-1',
    target_type: 'builtin',
    target_id: 'video_action_product',
    surface: 'portal'
  });
});

test('generation request options can target the workbench namespace', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'image-task-2',
      tenant_id: 'demo',
      user_id: 'demo-user',
      task_type: 'IMAGE',
      route_key: 'image_text_to_image',
      prompt: 'demo',
      status: 'PENDING',
      estimated_cost: 45,
      surface: 'workbench'
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await createImageGeneration('工作台图像任务', {
    targetType: 'builtin',
    targetId: 'image_text_to_image',
    surface: 'workbench'
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body.surface).toBe('workbench');
});

test('media workbench task fetches surface backend failures instead of local fallbacks', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({}) } as Response));

  await expect(fetchImageWorkbench('workbench')).rejects.toThrow('503');
  await expect(fetchVideoWorkbench('workbench')).rejects.toThrow('503');
  await expect(fetchAudioTasks('workbench')).rejects.toThrow('503');
});
