import React from 'react';
import { PhoneIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import Button from './Button';

interface EmergencyContactsProps {
  emergencyData?: {
    emergency_contacts: { [key: string]: string };
    red_flag_symptoms: string[];
    when_to_seek_immediate_care: string[];
    disclaimer: string;
  };
}

const EmergencyContacts: React.FC<EmergencyContactsProps> = ({ emergencyData }) => {
  const defaultEmergencyData = {
    emergency_contacts: {
      us: '911',
      uk: '999',
      eu: '112',
      poison_control_us: '1-800-222-1222'
    },
    red_flag_symptoms: [
      'Severe chest pain or pressure',
      'Difficulty breathing or shortness of breath',
      'Signs of stroke (face drooping, arm weakness, speech difficulty)',
      'Severe allergic reaction (anaphylaxis)',
      'Severe bleeding that won\'t stop',
      'Severe abdominal pain',
      'High fever with neck stiffness',
      'Loss of consciousness',
      'Severe burns',
      'Thoughts of self-harm or suicide'
    ],
    when_to_seek_immediate_care: [
      'Any life-threatening symptoms',
      'Severe pain that isn\'t improving',
      'High fever in infants under 3 months',
      'Severe dehydration',
      'Severe mental health crisis'
    ],
    disclaimer: 'If you are experiencing a medical emergency, call emergency services immediately. Do not rely on this AI system for emergency medical advice.'
  };

  const data = emergencyData || defaultEmergencyData;

  const callEmergency = (number: string) => {
    if (number.startsWith('1-800') || number.length > 5) {
      window.location.href = `tel:${number}`;
    } else {
      window.location.href = `tel:${number}`;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-red-600 mb-2">Emergency Information</h1>
        <p className="text-gray-600">Important emergency contacts and warning signs</p>
      </div>

      {/* Emergency Disclaimer */}
      <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-lg">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-2" />
          <p className="text-red-800 font-medium">
            If you are experiencing a medical emergency, call emergency services immediately!
          </p>
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Emergency Contacts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data.emergency_contacts).map(([location, number]) => (
            <div key={location} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <span className="font-medium text-gray-700">
                  {location.toUpperCase().replace('_', ' ')}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold text-red-600">{number}</span>
                <Button
                  onClick={() => callEmergency(number)}
                  size="small"
                  variant="danger"
                  className="flex items-center space-x-1"
                >
                  <PhoneIcon className="w-4 h-4" />
                  <span>Call</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Red Flag Symptoms */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Red Flag Symptoms - Call 911 Immediately</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {data.red_flag_symptoms.map((symptom, index) => (
            <div key={index} className="flex items-start space-x-2 p-2">
              <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
              <span className="text-gray-700">{symptom}</span>
            </div>
          ))}
        </div>
      </div>

      {/* When to Seek Immediate Care */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">When to Seek Immediate Care</h2>
        <div className="space-y-2">
          {data.when_to_seek_immediate_care.map((situation, index) => (
            <div key={index} className="flex items-start space-x-2 p-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
              <span className="text-gray-700">{situation}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Resources */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Additional Resources</h2>
        <div className="space-y-3">
          <div className="p-3 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800">Mental Health Crisis</h3>
            <p className="text-sm text-blue-700">
              National Suicide Prevention Lifeline: <strong>988</strong>
            </p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <h3 className="font-semibold text-green-800">Poison Control</h3>
            <p className="text-sm text-green-700">
              Call <strong>1-800-222-1222</strong> for poison emergencies
            </p>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <h3 className="font-semibold text-purple-800">Text Emergency Services</h3>
            <p className="text-sm text-purple-700">
              Text "911" to 911 if you cannot make a voice call
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-600 text-center">
          {data.disclaimer}
        </p>
      </div>
    </div>
  );
};

export default EmergencyContacts;
