import { afterEach, expect, test, vi } from 'vitest';
import {
  createChatSession,
  exportChatSession,
  fetchChatWorkbench,
  sendChatMessage,
  updateChatSession
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

test('chat workbench request includes session and user query params', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      tenant_id: 'demo',
      user_id: 'demo-user',
      sessions: [],
      active_session: null,
      models: []
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await fetchChatWorkbench('chat-123');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/chat/workbench?user_id=demo-user&session_id=chat-123');
});

test('chat message request sends the active model and content', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      session: {
        id: 'chat-123',
        title: '项目周报',
        messages: []
      },
      messages_created: []
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await sendChatMessage('chat-123', { content: '请整理本周进展', modelKey: 'general_text_default' });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    content: '请整理本周进展',
    model_key: 'general_text_default'
  });
});

test('chat export request uses markdown format', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      asset: {
        id: 'asset-1',
        url: '/storage/exports/demo/chat-1.md',
        storage_key: 'exports/demo/chat-1.md',
        file_name: 'chat-1.md'
      },
      message: {
        id: 'msg-3',
        role: 'assistant',
        content: 'Markdown export created: chat-1.md'
      }
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await exportChatSession('chat-123');

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toEqual({ format: 'markdown' });
});

test('chat session update sends the selected model and role', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'chat-123',
      title: '更新后的标题',
      messages: []
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await updateChatSession('chat-123', { title: '更新后的标题', modelKey: 'general_text_default', presetRole: 'assistant' });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    title: '更新后的标题',
    model_key: 'general_text_default',
    preset_role: 'assistant'
  });
});

test('chat session create uses the demo user by default', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'chat-123',
      title: '新对话',
      messages: []
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await createChatSession({ title: '新对话', modelKey: 'general_text_default' });

  const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
  expect(body).toMatchObject({
    title: '新对话',
    user_id: 'demo-user',
    model_key: 'general_text_default'
  });
});
