/**
 * Main layout component with navigation.
 */

import { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { ActivityStatusBar } from '@/components/ActivityStatusBar';
import { Navigation } from './Navigation';
import { ViewControlsProvider } from './ViewControlsContext';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="layout app-shell">
      <ViewControlsProvider>
        <Navigation />
        <ActivityStatusBar />
        <main className="layout-content" key={location.pathname}>
          {children}
        </main>
      </ViewControlsProvider>
    </div>
  );
}
