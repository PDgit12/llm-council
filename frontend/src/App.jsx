import { useState, useEffect, useRef } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import HomePage from './components/HomePage';
import { api } from './api';
import './App.css';

function AuthenticatedApp() {
  const { currentUser } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const pendingQueryRef = useRef(null);

  const loadConversations = async (autoSelectLatest = false) => {
    if (!currentUser) return;
    try {
      const convs = await api.listConversations();
      setConversations(convs);

      // Auto-select latest if requested and nothing currently selected
      if (autoSelectLatest && convs.length > 0 && !currentConversationId) {
        setCurrentConversationId(convs[0].id);
      }
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

  const handleSendMessage = async (content, attachments = []) => {
    if (!currentConversationId) return;

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
          case 'model_activity':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.model_activity = { ...(lastMsg.model_activity || {}), [event.data.model]: event.data.status };
              return { ...prev, messages };
            });
            break;

          case 'parallel_phase_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_partial':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = { ...(lastMsg.stage1 || {}), ...event.data };
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            updateLastMessage((msg) => {
              msg.stage1 = event.data;
              msg.loading.stage1 = false;
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_partial':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = { ...(lastMsg.stage2 || {}), ...event.data };
              return { ...prev, messages };
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

          case 'stage3_partial':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = { ...(lastMsg.stage3 || {}), ...event.data };
              return { ...prev, messages };
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

          case 'stage4_partial':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage4 = { ...(lastMsg.stage4 || {}), ...event.data };
              return { ...prev, messages };
            });
            break;

          case 'stage4_complete':
            updateLastMessage((msg) => {
              msg.stage4 = event.data;
              msg.loading.stage4 = false;
            });
            break;

          case 'stage5_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage5 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage5_partial':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage5 = { ...(lastMsg.stage5 || {}), ...event.data };
              return { ...prev, messages };
            });
            break;

          case 'stage5_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage5 = event.data;
              lastMsg.loading.stage5 = false;
              return { ...prev, messages };
            });
            break;

          case 'council_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.final_answer = event.data.final_answer;
              lastMsg.reasoning_factor = event.data.reasoning_factor;
              lastMsg.loading = { stage1: false, stage2: false, stage3: false, stage4: false };
              lastMsg.council_result = event.data;
              return { ...prev, messages };
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

  useEffect(() => {
    if (currentUser) {
      loadConversations(true); // Auto-select latest on login
    } else {
      setConversations([]);
      setCurrentConversationId(null);
      setCurrentConversation(null);
    }
  }, [currentUser]);

  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

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
      // Optimistically update conversations list
      const newMetadata = {
        id: newConv.id,
        created_at: newConv.created_at,
        title: newConv.title || 'New Task',
        message_count: 0
      };

      setConversations(prev => [newMetadata, ...prev]);

      // Immediately set the full conversation object to avoid "Initializing Council" spinner
      setCurrentConversation(newConv);
      setCurrentConversationId(newConv.id);

      return newConv.id;
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleGoHome = () => {
    setCurrentConversationId(null);
    setCurrentConversation(null);
  };

  if (!currentUser) {
    if (showLogin) {
      return <Login />;
    }
    return (
      <HomePage
        conversations={[]}
        onNewConversation={() => setShowLogin(true)}
        onSelectConversation={() => setShowLogin(true)}
        onExampleClick={(query) => {
          pendingQueryRef.current = query;
          setShowLogin(true);
        }}
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

function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

export default App;
