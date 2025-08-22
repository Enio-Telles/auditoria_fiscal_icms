import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Buscar elemento root
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

// Criar root e renderizar a aplicação
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
