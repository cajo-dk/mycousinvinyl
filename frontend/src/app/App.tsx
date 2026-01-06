import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  useMsal,
  AuthenticatedTemplate,
  UnauthenticatedTemplate,
} from '@azure/msal-react';
import { loginRequest } from '@/auth/authConfig';
import { Layout } from '@/components/Layout';
import { Loading } from '@/components/UI';
import { Home, Collection, Artists, Albums, Pressings, Settings, Profile, AlbumWizard } from '@/pages';
import { useIsAdmin } from '@/auth/useAdmin';
import './App.css';

function App() {
  const { instance } = useMsal();
  const { isAdmin, isLoading: isAdminLoading } = useIsAdmin();

  const handleLogin = async () => {
    try {
      await instance.loginPopup(loginRequest);
    } catch (e) {
      console.error('Login failed:', e);
    }
  };

  return (
    <Router>
      <div className="app">
        <AuthenticatedTemplate>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/collection" element={<Collection />} />
              <Route path="/artists" element={<Artists />} />
              <Route path="/albums" element={<Albums />} />
              <Route path="/pressings" element={<Pressings />} />
              <Route path="/album-wizard" element={<AlbumWizard />} />
              <Route path="/profile" element={<Profile />} />
              <Route
                path="/settings"
                element={
                  isAdminLoading ? (
                    <Loading message="Checking access..." />
                  ) : isAdmin ? (
                    <Settings />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </AuthenticatedTemplate>

        <UnauthenticatedTemplate>
          <div className="login-container">
            <div className="login-card">
              <h1>MyCousinVinyl</h1>
              <p className="login-subtitle">Your personal vinyl collection manager</p>
              <p className="login-description">
                Sign in with your Microsoft account to access your collection
              </p>
              <button onClick={handleLogin} className="login-button">
                <svg
                  width="21"
                  height="21"
                  viewBox="0 0 21 21"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="ms-logo"
                >
                  <rect width="10" height="10" fill="#F25022" />
                  <rect x="11" width="10" height="10" fill="#7FBA00" />
                  <rect y="11" width="10" height="10" fill="#00A4EF" />
                  <rect x="11" y="11" width="10" height="10" fill="#FFB900" />
                </svg>
                Sign in with Microsoft
              </button>
            </div>
          </div>
        </UnauthenticatedTemplate>
      </div>
    </Router>
  );
}

export default App;
