/**
 * API client for the Parallels backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';
export const API_BASE_URL = API_BASE;

export const api = {
  /**
   * List all explorations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    if (!response.ok) {
      throw new Error('Failed to list explorations');
    }
    return response.json();
  },

  /**
   * Create a new exploration.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
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
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
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
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`,
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to delete exploration');
    }
    return response.json();
  },
};
