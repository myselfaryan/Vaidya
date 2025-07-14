import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-lg">
      <h1 className="text-xl font-semibold">Vaidya Medical Assistant</h1>
      <p className="text-sm opacity-90">AI-powered medical information and guidance</p>
    </header>
  );
};

export default Header;
