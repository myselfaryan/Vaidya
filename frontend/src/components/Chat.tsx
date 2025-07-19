import React, { useState, useRef, useEffect, useCallback, FC, ReactElement } from 'react';
import { PaperAirplaneIcon, PaperClipIcon, XMarkIcon } from '@heroicons/react/24/solid';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import MessageBubble from './MessageBubble';
import LoadingSpinner from './LoadingSpinner';
import { apiService } from '../services/apiService';

interface Message {
  id: string;
  content: string;
  isFromUser: boolean;
  timestamp: Date;
  confidence?: number;
  sources?: any[];
  type?: 'user' | 'assistant' | 'system';
}

interface ChatProps {
  // Add any props if needed
}

const Chat: FC<ChatProps> = (): ReactElement => {
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
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error('File size should be less than 10MB');
        return;
      }
      setSelectedFile(file);
    }
  };

  const removeFile = (): void => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const uploadFile = async (): Promise<void> => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      await apiService.uploadDocument(
        selectedFile,
        (progressEvent: ProgressEvent) => {
          if (progressEvent.lengthComputable) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(progress);
          }
        }
      );

      toast.success('Document uploaded successfully!');
      removeFile();
      
      // Add a system message about the upload
      const systemMessage: Message = {
        id: `doc-${Date.now()}`,
        content: `Document "${selectedFile.name}" has been uploaded and processed.`,
        isFromUser: false,
        timestamp: new Date(),
        type: 'system'
      };
      
      setMessages(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('Error uploading file:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload document';
      toast.error(`Error: ${errorMessage}`);
      throw error;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };
  };

  const sendMessage = async (): Promise<void> => {
    if (!inputMessage.trim() && !selectedFile) return;

    // Handle file upload first if a file is selected
    if (selectedFile) {
      try {
        await uploadFile();
      } catch (error) {
        return; // Error already handled in uploadFile
      }
    }

    // If there's a message to send, send it
    if (inputMessage.trim()) {
      const userMessage: Message = {
        id: Date.now().toString(),
        content: inputMessage,
        isFromUser: true,
        timestamp: new Date(),
        type: 'user'
      };

      setMessages(prev => [...prev, userMessage]);
      setInputMessage('');
      setIsLoading(true);

      try {
        const response = await apiService.sendMessage(inputMessage);
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.data.answer || response.data.message || 'I received your message.',
          isFromUser: false,
          timestamp: new Date(),
          confidence: response.data.confidence,
          sources: response.data.sources,
          type: 'assistant'
        };

        setMessages(prev => [...prev, aiMessage]);
      } catch (error) {
        console.error('Error sending message:', error);
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'I apologize, but I\'m having trouble processing your request right now. Please try again later or consult with a healthcare professional.',
          isFromUser: false,
          timestamp: new Date(),
          type: 'system'
        };

        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
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
          <MessageBubble
            key={message.id}
            message={{
              id: message.id,
              content: message.content,
              isFromUser: message.isFromUser,
              timestamp: message.timestamp,
              confidence: message.confidence,
              sources: message.sources
            }}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        {/* File upload preview */}
        {selectedFile && (
          <div className="flex items-center justify-between p-3 mb-2 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <PaperClipIcon className="w-5 h-5 text-blue-500" />
              <span className="text-sm text-gray-700 truncate max-w-xs">
                {selectedFile.name}
              </span>
              <span className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            <button
              onClick={removeFile}
              className="p-1 text-gray-400 rounded-full hover:text-gray-600 hover:bg-gray-100"
              disabled={isUploading}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
        )}
        
        {/* Upload progress */}
        {isUploading && (
          <div className="w-full mb-2 bg-gray-200 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full bg-blue-600 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}
        
        {/* Input area */}
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Type your message..."
              disabled={isLoading || isUploading}
            />
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept=".pdf,.docx,.txt"
              disabled={isUploading}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 rounded-full hover:text-gray-600 hover:bg-gray-100"
            >
              <PaperClipIcon className="w-5 h-5" />
            </button>
          </div>
          <button
            onClick={sendMessage}
            disabled={isLoading || isUploading || (!inputMessage.trim() && !selectedFile)}
            className="flex items-center justify-center w-12 h-12 text-white bg-blue-500 rounded-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading || isUploading ? (
              <LoadingSpinner size="small" />
            ) : (
              <PaperAirplaneIcon className="w-5 h-5 transform rotate-90" />
            )}
          </button>
        </div>
        
        {/* File type hint */}
        <p className="mt-1 text-xs text-gray-500">
          Supports PDF, DOCX, TXT (Max 10MB)
        </p>
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
};

export default Chat;
