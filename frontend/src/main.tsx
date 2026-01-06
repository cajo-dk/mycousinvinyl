import React from 'react';
import ReactDOM from 'react-dom/client';
import { MsalProvider } from '@azure/msal-react';
import { PublicClientApplication, EventType } from '@azure/msal-browser';
import App from './app/App';
import { msalConfig } from './auth/authConfig';
import { configureMsalInstance } from './api/client';
import './app/index.css';

// Create MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL and render app
(async () => {
  // Handle redirect promise
  await msalInstance.initialize();

  // Configure API client with initialized MSAL instance
  configureMsalInstance(msalInstance);

  // Default to using the first account if no account is active on page load
  if (
    !msalInstance.getActiveAccount() &&
    msalInstance.getAllAccounts().length > 0
  ) {
    msalInstance.setActiveAccount(msalInstance.getAllAccounts()[0]);
  }

  // Listen for account changes
  msalInstance.addEventCallback((event) => {
    if (
      event.eventType === EventType.LOGIN_SUCCESS &&
      event.payload &&
      'account' in event.payload
    ) {
      const account = event.payload.account;
      msalInstance.setActiveAccount(account || null);
    }
  });

  // Render the app
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
})();
