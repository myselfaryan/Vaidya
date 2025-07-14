import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, MicrophoneIcon } from '@heroicons/react/24/solid';
import MessageBubble from './MessageBubble';
import LoadingSpinner from './LoadingSpinner';
import Button from './Button';

interface Message {
  id: string;
  content: string;
  isFromUser: boolean;
  timestamp: Date;
  confidence?: number;
  sources?: any[];
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m Vaidya, your AI medical assistant. I can help you with health questions, symptom analysis, and medical information. How can I help you today?',
      isFromUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      isFromUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Simulate API call to backend
      const response = await fetch('/api/v1/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          question: inputMessage,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.answer,
          isFromUser: false,
          timestamp: new Date(),
          confidence: data.confidence,
          sources: data.sources,
        };

        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'I apologize, but I\'m having trouble processing your request right now. Please try again later or consult with a healthcare professional.',
        isFromUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 shadow-lg">
        <h1 className="text-xl font-semibold">Vaidya Medical Assistant</h1>
        <p className="text-sm opacity-90">AI-powered medical information and guidance</p>
      </div>

      {/* Medical Disclaimer */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 text-sm">
        <p className="text-yellow-800">
          <strong>Medical Disclaimer:</strong> This AI provides educational information only. 
          Always consult healthcare professionals for medical decisions. In emergencies, call 911.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <LoadingSpinner size="small" message="Analyzing..." />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex items-center space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your health concerns..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={1}
            disabled={isLoading}
          />
          
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
          
          <button
            className="bg-gray-200 text-gray-700 p-2 rounded-lg hover:bg-gray-300"
            title="Voice input (coming soon)"
          >
            <MicrophoneIcon className="w-5 h-5" />
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default Chat;
