import React from 'react';
import ReactDOM from 'react-dom/client';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import ErrorBoundary from './components/ErrorBoundary';
import Router from './router';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <WebSocketProvider>
          <Router />
        </WebSocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

