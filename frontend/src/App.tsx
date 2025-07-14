import React, { useState } from 'react';
import Chat from './components/Chat';
import Header from './components/Header';
import SymptomChecker from './components/SymptomChecker';
import EmergencyContacts from './components/EmergencyContacts';
import LoginForm from './components/LoginForm';
import Button from './components/Button';
import './styles/index.css';

type View = 'chat' | 'symptoms' | 'emergency' | 'login';

function App() {
  const [currentView, setCurrentView] = useState<View>('chat');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [symptomResults, setSymptomResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (credentials: { username: string; password: string }) => {
    setIsLoading(true);
    try {
      // Mock login - in real app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsLoggedIn(true);
      setCurrentView('chat');
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleSymptomAnalysis = async (symptoms: string[]) => {
    setIsLoading(true);
    try {
      // Mock API call - in real app, this would call the backend
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock response
      const mockResults = {
        symptoms,
        urgency_level: 'medium',
        possible_conditions: [
          { name: 'Common Cold', confidence: 0.7 },
          { name: 'Flu', confidence: 0.5 }
        ],
        recommendations: [
          'Get plenty of rest',
          'Stay hydrated',
          'Monitor symptoms',
          'Consider seeing a healthcare provider if symptoms worsen'
        ],
        disclaimer: 'This is for educational purposes only. Always consult with a healthcare professional for medical advice.'
      };
      
      setSymptomResults(mockResults);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const renderNavigation = () => {
    if (!isLoggedIn) return null;
    
    return (
      <nav className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex space-x-4">
          <Button
            variant={currentView === 'chat' ? 'primary' : 'secondary'}
            size="small"
            onClick={() => setCurrentView('chat')}
          >
            Chat
          </Button>
          <Button
            variant={currentView === 'symptoms' ? 'primary' : 'secondary'}
            size="small"
            onClick={() => setCurrentView('symptoms')}
          >
            Symptom Checker
          </Button>
          <Button
            variant={currentView === 'emergency' ? 'primary' : 'secondary'}
            size="small"
            onClick={() => setCurrentView('emergency')}
          >
            Emergency
          </Button>
          <Button
            variant="secondary"
            size="small"
            onClick={() => {
              setIsLoggedIn(false);
              setCurrentView('login');
            }}
            className="ml-auto"
          >
            Logout
          </Button>
        </div>
      </nav>
    );
  };

  const renderContent = () => {
    if (!isLoggedIn) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <LoginForm onLogin={handleLogin} isLoading={isLoading} />
        </div>
      );
    }

    switch (currentView) {
      case 'chat':
        return (
          <div className="h-screen flex flex-col">
            <Chat />
          </div>
        );
      case 'symptoms':
        return (
          <div className="min-h-screen bg-gray-50 py-8">
            <SymptomChecker
              onAnalyze={handleSymptomAnalysis}
              isLoading={isLoading}
              results={symptomResults}
            />
          </div>
        );
      case 'emergency':
        return (
          <div className="min-h-screen bg-gray-50 py-8">
            <EmergencyContacts />
          </div>
        );
      default:
        return (
          <div className="h-screen flex flex-col">
            <Chat />
          </div>
        );
    }
  };

  return (
    <div className="App">
      <Header />
      {renderNavigation()}
      {renderContent()}
    </div>
  );
}

export default App;
