import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import HomePage from './components/HomePage';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showLanding, setShowLanding] = useState(true);
  const pendingQueryRef = useRef(null);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const handleSendMessage = async (content, attachments = []) => {
    if (!currentConversationId) return;

    // Helper for immutable state updates on the last message
    const updateLastMessage = (updater) => {
      setCurrentConversation((prev) => {
        const messages = [...(prev.messages || [])];
        if (messages.length === 0) return prev;

        const lastIndex = messages.length - 1;
        // Create a shallow copy of the last message
        const lastMsg = { ...messages[lastIndex] };

        // Create a shallow copy of the loading object if it exists
        if (lastMsg.loading) {
          lastMsg.loading = { ...lastMsg.loading };
        }

        // Apply updates (mutating the copies is fine)
        updater(lastMsg);

        messages[lastIndex] = lastMsg;
        return { ...prev, messages };
      });
    };

    setIsLoading(true);
    try {
      const userMessage = { role: 'user', content, attachments };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []), userMessage],
      }));

      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        stage4: null,
        domains: [],
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
          stage4: false,
        },
      };

      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []), assistantMessage],
      }));

      await api.sendMessageStream(currentConversationId, { content, attachments }, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            updateLastMessage((msg) => {
              msg.loading.stage1 = true;
              if (event.domains) msg.domains = event.domains;
            });
            break;

          case 'stage1_complete':
            updateLastMessage((msg) => {
              msg.stage1 = event.data;
              msg.loading.stage1 = false;
            });
            break;

          case 'stage2_start':
            updateLastMessage((msg) => {
              msg.loading.stage2 = true;
              if (event.domains) msg.domains = event.domains;
            });
            break;

          case 'stage2_complete':
            updateLastMessage((msg) => {
              msg.stage2 = event.data;
              msg.loading.stage2 = false;
            });
            break;

          case 'stage3_start':
            updateLastMessage((msg) => {
              msg.loading.stage3 = true;
            });
            break;

          case 'stage3_complete':
            updateLastMessage((msg) => {
              msg.stage3 = event.data;
              msg.loading.stage3 = false;
            });
            break;

          case 'stage4_start':
            updateLastMessage((msg) => {
              msg.loading.stage4 = true;
            });
            break;

          case 'stage4_complete':
            updateLastMessage((msg) => {
              msg.stage4 = event.data;
              msg.loading.stage4 = false;
            });
            break;

          case 'council_start':
            updateLastMessage((msg) => {
              msg.loading.stage1 = true; // Show *some* loading indicator
            });
            break;

          case 'council_complete':
            updateLastMessage((msg) => {
              msg.final_answer = event.data.final_answer;
              msg.reasoning_factor = event.data.reasoning_factor;

              // Clear loading states
              msg.loading = {
                stage1: false,
                stage2: false,
                stage3: false,
                stage4: false
              };

              // Store full result if needed for debugging or advanced view
              msg.council_result = event.data;
            });
            break;

          case 'title_complete':
            loadConversations();
            break;

          case 'complete':
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  // When conversation loads and there's a pending query, auto-send it
  useEffect(() => {
    if (currentConversation && pendingQueryRef.current && currentConversation.messages?.length === 0) {
      const query = pendingQueryRef.current;
      pendingQueryRef.current = null;
      handleSendMessage(query);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentConversation]);

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      setShowLanding(false);
      return newConv.id;
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleExampleClick = async (query) => {
    pendingQueryRef.current = query;
    await handleNewConversation();
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    setShowLanding(false);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
        setShowLanding(true);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleGoHome = () => {
    setCurrentConversationId(null);
    setCurrentConversation(null);
    setShowLanding(true);
  };

  // Full-screen landing page (no sidebar)
  if (showLanding && !currentConversationId) {
    return (
      <HomePage
        conversations={conversations}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onExampleClick={handleExampleClick}
      />
    );
  }

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onGoHome={handleGoHome}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;
