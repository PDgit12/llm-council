import { auth } from './firebase';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
export const API_BASE_URL = API_BASE;

/**
 * Helper to get Auth headers
 */
const getHeaders = async () => {
  const token = await auth.currentUser?.getIdToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

export const api = {
  /**
   * List all explorations.
   */
  async listConversations() {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE}/api/conversations`, { headers });
    if (!response.ok) {
      throw new Error('Failed to list explorations');
    }
    return response.json();
  },

  /**
   * Create a new exploration.
   */
  async createConversation() {
    const headers = await getHeaders();
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers,
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to create exploration');
    }
    return response.json();
  },

  /**
   * Get a specific exploration.
   */
  async getConversation(conversationId) {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      { headers }
    );
    if (!response.ok) {
      throw new Error('Failed to get exploration');
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates via SSE.
   * @param {string} conversationId
   * @param {object} payload - { content, attachments?, target_domain? }
   * @param {function} onEvent - (eventType, data) => void
   */
  async sendMessageStream(conversationId, payload, onEvent) {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    const processLine = (line) => {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        try {
          const event = JSON.parse(data);
          onEvent(event.type, event);
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      }
    };

    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        processLine(line);
      }
    }

    if (buffer) {
      processLine(buffer);
    }
  },

  /**
   * Upload a file.
   */
  async uploadFile(file) {
    const authHeaders = await getHeaders();
    // Remove Content-Type so browser sets it with boundary for FormData
    delete authHeaders['Content-Type'];
    
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload file');
    }
    return response.json();
  },

  /**
   * Delete an exploration.
   */
  async deleteConversation(conversationId) {
    const headers = await getHeaders();
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      {
        method: 'DELETE',
        headers
      }
    );
    if (!response.ok) {
      throw new Error('Failed to delete exploration');
    }
    return response.json();
  },
};
