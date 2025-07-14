import React, { useState } from 'react';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface SymptomCheckerProps {
  onAnalyze: (symptoms: string[]) => Promise<void>;
  isLoading?: boolean;
  results?: any;
}

const SymptomChecker: React.FC<SymptomCheckerProps> = ({ onAnalyze, isLoading = false, results }) => {
  const [symptoms, setSymptoms] = useState<string[]>(['']);
  const [error, setError] = useState('');

  const addSymptom = () => {
    setSymptoms([...symptoms, '']);
  };

  const removeSymptom = (index: number) => {
    if (symptoms.length > 1) {
      setSymptoms(symptoms.filter((_, i) => i !== index));
    }
  };

  const updateSymptom = (index: number, value: string) => {
    const newSymptoms = [...symptoms];
    newSymptoms[index] = value;
    setSymptoms(newSymptoms);
  };

  const handleAnalyze = async () => {
    const validSymptoms = symptoms.filter(s => s.trim() !== '');
    
    if (validSymptoms.length === 0) {
      setError('Please enter at least one symptom');
      return;
    }

    setError('');
    try {
      await onAnalyze(validSymptoms);
    } catch (error) {
      setError('Failed to analyze symptoms. Please try again.');
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'emergency':
        return 'bg-red-100 border-red-400 text-red-700';
      case 'high':
        return 'bg-orange-100 border-orange-400 text-orange-700';
      case 'medium':
        return 'bg-yellow-100 border-yellow-400 text-yellow-700';
      case 'low':
        return 'bg-green-100 border-green-400 text-green-700';
      default:
        return 'bg-gray-100 border-gray-400 text-gray-700';
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center mb-6">Symptom Checker</h2>
      
      <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          <strong>Important:</strong> This tool is for informational purposes only. 
          It should not replace professional medical advice, diagnosis, or treatment.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="space-y-4 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Enter your symptoms:
        </label>
        
        {symptoms.map((symptom, index) => (
          <div key={index} className="flex items-center space-x-2">
            <input
              type="text"
              value={symptom}
              onChange={(e) => updateSymptom(index, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., headache, fever, fatigue"
              disabled={isLoading}
            />
            
            {symptoms.length > 1 && (
              <button
                type="button"
                onClick={() => removeSymptom(index)}
                className="p-2 text-red-600 hover:text-red-800"
                disabled={isLoading}
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            )}
          </div>
        ))}

        <button
          type="button"
          onClick={addSymptom}
          className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
          disabled={isLoading}
        >
          <PlusIcon className="w-4 h-4" />
          <span>Add another symptom</span>
        </button>
      </div>

      <Button
        onClick={handleAnalyze}
        disabled={isLoading}
        className="w-full"
      >
        {isLoading ? <LoadingSpinner size="small" /> : 'Analyze Symptoms'}
      </Button>

      {results && (
        <div className="mt-6 space-y-4">
          {/* Urgency Level */}
          <div className={`p-4 rounded-lg border ${getUrgencyColor(results.urgency_level)}`}>
            <h3 className="font-semibold">Urgency Level: {results.urgency_level.toUpperCase()}</h3>
          </div>

          {/* Possible Conditions */}
          {results.possible_conditions && results.possible_conditions.length > 0 && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="font-semibold mb-2">Possible Conditions:</h3>
              <ul className="space-y-1">
                {results.possible_conditions.map((condition: any, index: number) => (
                  <li key={index} className="text-sm">
                    • {condition.name || condition} 
                    {condition.confidence && ` (${Math.round(condition.confidence * 100)}% confidence)`}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {results.recommendations && results.recommendations.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-semibold mb-2">Recommendations:</h3>
              <ul className="space-y-1">
                {results.recommendations.map((rec: string, index: number) => (
                  <li key={index} className="text-sm">• {rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-600">{results.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SymptomChecker;
