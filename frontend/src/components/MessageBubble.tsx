import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface MessageBubbleProps {
  message: {
    id: string;
    content: string;
    isFromUser: boolean;
    timestamp: Date;
    confidence?: number;
    sources?: any[];
  };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceIcon = (confidence?: number) => {
    if (!confidence) return null;
    if (confidence >= 0.7) {
      return <CheckCircleIcon className="w-4 h-4 text-green-600" />;
    }
    return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-600" />;
  };

  return (
    <div className={`flex ${message.isFromUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          message.isFromUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap">
          {message.content}
        </div>
        
        {/* Confidence indicator for AI messages */}
        {!message.isFromUser && message.confidence && (
          <div className="flex items-center mt-2 text-xs">
            {getConfidenceIcon(message.confidence)}
            <span className={`ml-1 ${getConfidenceColor(message.confidence)}`}>
              Confidence: {Math.round(message.confidence * 100)}%
            </span>
          </div>
        )}
        
        {/* Sources for AI messages */}
        {!message.isFromUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 text-xs text-gray-600">
            <span className="font-medium">Sources: </span>
            {message.sources.length} reference(s)
          </div>
        )}
        
        <div className="text-xs opacity-75 mt-1">
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
