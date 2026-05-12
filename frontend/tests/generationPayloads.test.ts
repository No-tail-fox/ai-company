import { afterEach, expect, test, vi } from 'vitest';
import {
  createImageGeneration,
  createVideoGeneration,
  fetchWorkbenchCapabilities,
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
    routeKey: 'legacy-route',
    options: { size: '1024x1024', quality: 'high', n: 2 }
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    prompt: '生成商品海报',
    user_id: 'demo-user',
    route_key: 'legacy-route',
    request_key: 'image-1',
    target_type: 'builtin',
    target_id: 'image_action_poster',
    surface: 'portal',
    options: { size: '1024x1024', quality: 'high', n: 2 }
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
    routeKey: 'legacy-route',
    options: { size: '1280x720', seconds: 8 }
  });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    prompt: '生成新品视频',
    user_id: 'demo-user',
    route_key: 'legacy-route',
    request_key: 'video-1',
    target_type: 'builtin',
    target_id: 'video_action_product',
    surface: 'portal',
    options: { size: '1280x720', seconds: 8 }
  });
});

test('workbench capabilities normalize grouped managed records', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      groups: {
        image: [
          {
            target_type: 'content_item',
            target_key: 'image-tool-poster',
            title: '海报生成',
            enabled: true,
            callable: true,
            unavailable_reason: '',
            effective_point_cost: 45,
            model_config: { model_key: 'image_text_to_image', display_name: 'GPT Image' }
          }
        ]
      }
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  const payload = await fetchWorkbenchCapabilities('workbench');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/workbench/capabilities?surface=workbench');
  expect(payload.groups.image[0]).toMatchObject({
    targetType: 'content_item',
    targetKey: 'image-tool-poster',
    title: '海报生成',
    enabled: true,
    callable: true,
    effectivePointCost: 45,
    modelConfig: { modelKey: 'image_text_to_image' }
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
