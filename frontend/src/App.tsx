import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './Layout';
import { Dashboard } from './pages/Dashboard';
import { CreateProject } from './pages/CreateProject';
import { History } from './pages/History';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Settings from './pages/Settings';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = localStorage.getItem('access_token');
  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AuthRoute({ children }: { children: React.ReactNode }) {
  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthRoute><Login /></AuthRoute>} />
        <Route path="/signup" element={<AuthRoute><Signup /></AuthRoute>} />
        
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateProject />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
