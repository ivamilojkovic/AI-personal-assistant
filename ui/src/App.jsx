import { useState, useRef, useEffect, useCallback } from 'react';
import { ClientFactory } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

const EMAIL_ASSISTANT_URL = import.meta.env.VITE_EMAIL_ASSISTANT_URL || 'http://localhost:9001';

function App() {
  const [conversations, setConversations] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [clientError, setClientError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const clientRef = useRef(null);

  // Subscriptions tab state
  const [activeTab, setActiveTab] = useState('chat');
  const [subscriptions, setSubscriptions] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [unseenSubCount, setUnseenSubCount] = useState(0);

  // Initialize A2A client on mount
  useEffect(() => {
    const initClient = async () => {
      try {
        const orchestratorUrl = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:9000';
        console.log('Initializing A2A client for:', orchestratorUrl);
        
        const factory = new ClientFactory();
        const client = await factory.createFromUrl(orchestratorUrl);
        clientRef.current = client;
        
        console.log('✓ A2A client initialized successfully');
        setClientError(null);
      } catch (error) {
        console.error('Failed to initialize A2A client:', error);
        setClientError(`Failed to connect to orchestrator: ${error.message}`);
      }
    };

    initClient();
  }, []);

  // Scroll to bottom when conversations change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // ------------------------------------------------------------------ //
  // Subscription helpers                                                //
  // ------------------------------------------------------------------ //

  const loadSubscriptions = useCallback(async () => {
    try {
      const res = await fetch(`${EMAIL_ASSISTANT_URL}/subscriptions`);
      const data = await res.json();
      setSubscriptions(data.subscriptions || []);
    } catch (e) {
      console.error('Failed to load subscriptions', e);
    }
  }, []);

  const pollSubscriptions = useCallback(async () => {
    try {
      const res = await fetch(`${EMAIL_ASSISTANT_URL}/subscriptions/poll`);
      const data = await res.json();
      setSubscriptions(data.all_subscriptions || []);
      if (activeTab !== 'subscriptions' && data.new_count > 0) {
        setUnseenSubCount(prev => prev + data.new_count);
      }
    } catch (e) {
      console.error('Poll failed', e);
    }
  }, [activeTab]);

  const scanSubscriptions = async (days) => {
    setIsScanning(true);
    try {
      const res = await fetch(`${EMAIL_ASSISTANT_URL}/subscriptions/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days }),
      });
      const data = await res.json();
      setSubscriptions(data.all_subscriptions || []);
    } catch (e) {
      console.error('Scan failed', e);
    } finally {
      setIsScanning(false);
    }
  };

  const unsubscribeItem = async (id) => {
    try {
      const res = await fetch(`${EMAIL_ASSISTANT_URL}/subscriptions/${id}/unsubscribe`, {
        method: 'POST',
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || 'Unsubscribe failed. You may need to do it manually.');
        setSubscriptions(prev =>
          prev.map(s => s.id === id ? { ...s, unsub_failed: true } : s)
        );
        return;
      }
      const data = await res.json();
      setSubscriptions(prev =>
        prev.map(s => s.id === id ? { ...s, status: 'unsubscribed', unsubscribed_at: data.subscription?.unsubscribed_at } : s)
      );
    } catch (e) {
      console.error('Unsubscribe failed', e);
    }
  };

  const keepItem = async (id) => {
    try {
      await fetch(`${EMAIL_ASSISTANT_URL}/subscriptions/${id}/keep`, { method: 'POST' });
      setSubscriptions(prev =>
        prev.map(s => s.id === id ? { ...s, status: 'kept' } : s)
      );
    } catch (e) {
      console.error('Keep failed', e);
    }
  };

  // Load subscriptions on mount and start polling every 5 min
  useEffect(() => {
    loadSubscriptions();
    const interval = setInterval(pollSubscriptions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // When switching to subscriptions tab, clear unseen badge and load fresh
  useEffect(() => {
    if (activeTab === 'subscriptions') {
      setUnseenSubCount(0);
      loadSubscriptions();
    }
  }, [activeTab]);

  // ------------------------------------------------------------------ //

  const parseResponse = (text) => {
    // Extract skill name from response
    let skillName = 'Assistant Response';
    const skillMatch = text.match(/executed\s+(?:skill:\s*)?(\w+)/i);
    if (skillMatch) {
      const skill = skillMatch[1];
      // Convert skill_id to readable name
      if (skill === 'write_email') skillName = 'Email Draft';
      else if (skill === 'send_email') skillName = 'Email Sent';
      else if (skill === 'classify_email') skillName = 'Email Classification';
      else if (skill === 'classify_emails') skillName = 'Email Classification';
      else skillName = skill.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // Try to extract email details from response
    const emailPattern = {
      to: /(?:To:|Recipient:|Email (?:sent|drafted) to:?|to)\s+([^\n,]+)/i,
      subject: /(?:Subject:|Re:)\s*([^\n]+)/i,
      body: /(?:Body:|Content:|Message:)\s*([\s\S]+?)(?=\n\n|\n(?:To:|Subject:|---)|$)/i,
    };

    const email = {};
    
    for (const [key, pattern] of Object.entries(emailPattern)) {
      const match = text.match(pattern);
      if (match) {
        email[key] = match[1].trim();
      }
    }

    // Check if this is an email-related response
    if (text.match(/email|classification|classify/i) || Object.keys(email).length > 0) {
      email.isEmail = true;
      email.skillName = skillName;
    }

    return { email, skillName };
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (!clientRef.current) {
      setConversations(prev => [...prev, {
        id: uuidv4(),
        request: input.trim(),
        response: '❌ A2A client not initialized. Please refresh the page or check the orchestrator URL.',
        timestamp: new Date(),
        error: true
      }]);
      return;
    }

    const userMessage = input.trim();
    const conversationId = uuidv4();
    setInput('');
    
    // Add request to conversations
    setConversations(prev => [...prev, {
      id: conversationId,
      request: userMessage,
      response: null,
      timestamp: new Date(),
      isLoading: true
    }]);
    
    setIsLoading(true);

    try {
      console.log('Sending message via A2A SDK:', userMessage);
      
      const sendParams = {
        message: {
          messageId: uuidv4(),
          role: 'user',
          parts: [{ kind: 'text', text: userMessage }],
          kind: 'message',
        },
        metadata: {
          skill_id: 'orchestrate',
          input_params: { request: userMessage }
        }
      };

      console.log('A2A Request:', JSON.stringify(sendParams, null, 2));

      const response = await clientRef.current.sendMessage(sendParams);
      
      console.log('A2A Response:', JSON.stringify(response, null, 2));

      let assistantMessage = 'No response received';

      if (response.parts && response.parts.length > 0) {
        const textPart = response.parts.find(part => part.kind === 'text');
        if (textPart && textPart.text) {
          assistantMessage = textPart.text;
        }
      } else if (response.events) {
        for (const event of response.events) {
          if (event.data?.text) {
            assistantMessage = event.data.text;
            break;
          }
        }
      }

      const isError =
        assistantMessage.trim().startsWith('❌') ||
        assistantMessage.includes('**Error:**');

      // Parse email details from response
      const { email: emailDetails, skillName } = parseResponse(assistantMessage);

      // Update conversation with response
      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? {
              ...conv,
              response: assistantMessage,
              emailDetails,
              skillName,
              error: isError, 
              isLoading: false
            }
          : conv
      ));

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = `❌ Error: ${error.message}\n\nPossible causes:\n1. Orchestrator not running\n2. CORS not configured\n3. Network issue`;
      
      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? {
              ...conv,
              response: assistantMessage,
              emailDetails,
              skillName,
              error: isError,
              isLoading: false
            }
          : conv
      ));

    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* Animated background */}
      <div className="background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="logo">
            <div className="logo-icon">
              <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
                <circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="2" opacity="0.5"/>
                <circle cx="50" cy="50" r="20" stroke="currentColor" strokeWidth="3"/>
                <circle cx="50" cy="35" r="3" fill="currentColor"/>
                <circle cx="35" cy="50" r="3" fill="currentColor"/>
                <circle cx="65" cy="50" r="3" fill="currentColor"/>
                <circle cx="50" cy="65" r="3" fill="currentColor"/>
                <line x1="50" y1="35" x2="50" y2="20" stroke="currentColor" strokeWidth="2"/>
                <line x1="35" y1="50" x2="20" y2="50" stroke="currentColor" strokeWidth="2"/>
                <line x1="65" y1="50" x2="80" y2="50" stroke="currentColor" strokeWidth="2"/>
                <line x1="50" y1="65" x2="50" y2="80" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </div>
            <div className="logo-text">
              <h1>AI Personal Assistant</h1>
              <p className="subtitle">Powered by MCP, A2A, and LangGraph</p>
            </div>
          </div>
        </header>

        {/* Tab bar */}
        <div className="tab-bar">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={`tab-btn ${activeTab === 'subscriptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('subscriptions')}
          >
            Subscriptions
            {unseenSubCount > 0 && (
              <span className="tab-badge">{unseenSubCount}</span>
            )}
          </button>
        </div>

        {/* Connection error banner */}
        {clientError && activeTab === 'chat' && (
          <div className="error-banner">
            ⚠️ {clientError}
          </div>
        )}

        {/* Subscriptions panel */}
        {activeTab === 'subscriptions' && (
          <div className="subscriptions-panel">
            <div className="subs-header">
              <div className="scan-buttons">
                <button
                  className="scan-btn"
                  onClick={() => scanSubscriptions(7)}
                  disabled={isScanning}
                >
                  {isScanning ? 'Scanning…' : 'Scan last 7 days'}
                </button>
                <button
                  className="scan-btn"
                  onClick={() => scanSubscriptions(30)}
                  disabled={isScanning}
                >
                  {isScanning ? 'Scanning…' : 'Scan last 30 days'}
                </button>
              </div>
              <span className="polling-indicator">↻ Live</span>
            </div>

            {(() => {
              const pending = subscriptions.filter(s => s.status === 'pending');
              const unsubscribed = subscriptions.filter(s => s.status === 'unsubscribed');
              const kept = subscriptions.filter(s => s.status === 'kept');

              return (
                <>
                  <div className="subs-section">
                    <h3 className="subs-section-title">
                      Pending ({pending.length})
                    </h3>
                    {pending.length === 0 && (
                      <p className="subs-empty">No pending subscriptions. Run a scan to detect new ones.</p>
                    )}
                    {pending.map(sub => (
                      <div key={sub.id} className={`sub-card ${sub.unsubscribe_path === 'auto' ? 'auto' : 'manual'}`}>
                        <div className="sub-card-top">
                          <div className="sub-info">
                            <span className="sub-path-icon">
                              {sub.unsubscribe_path === 'auto' ? '⚡' : '✋'}
                            </span>
                            <div>
                              <div className="sub-name">{sub.sender_name || sub.sender_email}</div>
                              <div className="sub-email">{sub.sender_email}</div>
                            </div>
                          </div>
                          {sub.unsubscribe_path === 'manual' && (
                            <div className="confidence-wrap">
                              <span className="confidence-pct">{sub.confidence}%</span>
                              <div className="confidence-bar">
                                <div
                                  className="confidence-fill"
                                  style={{ width: `${sub.confidence}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="sub-card-bottom">
                          <span className="sub-last-received">
                            Last received: {sub.last_received ? new Date(sub.last_received).toLocaleDateString() : '—'}
                            {' · '}
                            {sub.unsubscribe_path === 'auto'
                              ? (sub.one_click ? 'one-click unsubscribe' : 'can auto-unsubscribe')
                              : 'manual — unsubscribe in Gmail'}
                          </span>
                          <div className="sub-actions">
                            {sub.unsubscribe_path === 'auto' && !sub.unsub_failed && (
                              <button className="btn-unsub" onClick={() => unsubscribeItem(sub.id)}>
                                Unsubscribe
                              </button>
                            )}
                            {(sub.unsubscribe_path === 'manual' || sub.unsub_failed) && sub.message_id && (
                              <a
                                className="btn-view-gmail"
                                href={`https://mail.google.com/mail/u/0/#all/${sub.message_id}`}
                                target="_blank"
                                rel="noreferrer"
                              >
                                View in Gmail →
                              </a>
                            )}
                            <button className="btn-keep" onClick={() => keepItem(sub.id)}>
                              Keep
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {unsubscribed.length > 0 && (
                    <details className="subs-section unsubscribed-section">
                      <summary className="subs-section-title">
                        Unsubscribed ({unsubscribed.length})
                      </summary>
                      {unsubscribed.map(sub => (
                        <div key={sub.id} className="unsubscribed-item">
                          <span>✓ {sub.sender_name || sub.sender_email}</span>
                          <span className="sub-date">
                            {sub.unsubscribed_at ? new Date(sub.unsubscribed_at).toLocaleDateString() : '—'}
                          </span>
                        </div>
                      ))}
                    </details>
                  )}

                  {kept.length > 0 && (
                    <details className="subs-section kept-section">
                      <summary className="subs-section-title">
                        Kept ({kept.length})
                      </summary>
                      {kept.map(sub => (
                        <div key={sub.id} className="unsubscribed-item">
                          <span>{sub.sender_name || sub.sender_email}</span>
                        </div>
                      ))}
                    </details>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {/* Main content area (chat) */}
        {activeTab === 'chat' && (<div className="main-content">
          {conversations.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">✨</div>
              <h2>How can I help you today?</h2>
              <p>Ask me to write emails, classify messages, or manage your tasks</p>
              <div className="suggestions">
                <button 
                  className="suggestion"
                  onClick={() => setInput('Write a professional email to client@example.com about our project status')}
                >
                  📧 Draft an email
                </button>
                <button 
                  className="suggestion"
                  onClick={() => setInput('Classify my emails from last week')}
                >
                  🏷️ Classify emails
                </button>
              </div>
            </div>
          ) : (
            <div className="conversations-container">
              {conversations.map((conv, index) => (
                <div key={conv.id} className="conversation-row">
                  {/* Left column - User request */}
                  <div className="request-column">
                    <div className="request-header">
                      <span className="request-label">Your Request</span>
                      <span className="request-time">
                        {conv.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className="request-content">
                      <div className="request-icon">👤</div>
                      <div className="request-text">{conv.request}</div>
                    </div>
                  </div>

                  {/* Right column - AI response */}
                  <div className="response-column">
                    <div className="response-header">
                      <span className="response-label">Assistant Response</span>
                      {!conv.isLoading && (
                        <span className="response-status">
                          {conv.error ? '❌' : '✅'}
                        </span>
                      )}
                    </div>
                    
                    {conv.isLoading ? (
                      <div className="response-loading">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                        <span className="loading-text">Processing your request...</span>
                      </div>
                    ) : (
                      <div className="response-content">
                        {conv.emailDetails?.isEmail ? (
                          <div className="email-preview">
                            <div className="email-preview-header">
                              <span className="email-icon">
                                {conv.skillName?.includes('Classification') ? '🏷️' : '📧'}
                              </span>
                              <span className="email-title">{conv.skillName || 'Email Response'}</span>
                            </div>

                            <div className="email-full-response">
                              <details>
                                <summary>View full response</summary>
                                <pre>{conv.response}</pre>
                              </details>
                            </div>
                          </div>
                        ) : (
                          <div className="text-response">
                            <div className="response-text">{conv.response}</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>)}

        {/* Input area (chat only) */}
        {activeTab === 'chat' && (<div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={conversations.length === 0 ? "Ask me anything..." : "What would you like to do next?"}
              disabled={isLoading || clientError}
              rows="1"
            />
            <button 
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || clientError}
              className="send-button"
            >
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
          <div className="input-hint">
            Press <kbd>Enter</kbd> to send • <kbd>Shift + Enter</kbd> for new line
          </div>
        </div>)}
      </div>
    </div>
  );
}

export default App;
