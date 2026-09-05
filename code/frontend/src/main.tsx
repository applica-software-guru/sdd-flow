import './i18n';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ThemeProvider } from './context/theme-context';
import { ToastProvider } from './context/toast-context';
import PwaStatus from './components/pwa-status';
import ToastContainer from './components/toast-container';
import App from './app';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <App />
        <PwaStatus />
        <ToastContainer />
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>
);
