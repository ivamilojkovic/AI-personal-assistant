import { useState, useRef, useEffect } from 'react';
import { ClientFactory } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [clientError, setClientError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const clientRef = useRef(null);

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

        {/* Connection error banner */}
        {clientError && (
          <div className="error-banner">
            ⚠️ {clientError}
          </div>
        )}

        {/* Main content area */}
        <div className="main-content">
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
        </div>

        {/* Input area */}
        <div className="input-container">
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
        </div>
      </div>
    </div>
  );
}

export default App;
