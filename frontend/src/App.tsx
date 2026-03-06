import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import DashboardLayout from './layout/DashboardLayout';
import Overview from './pages/dashboard/Overview';
import HiringTrends from './pages/dashboard/HiringTrends';
import SkillsIntelligence from './pages/dashboard/SkillsIntelligence';
import AIVulnerability from './pages/dashboard/AIVulnerability';
import WorkerIntelligence from './pages/dashboard/WorkerIntelligence';
import ReskillingPath from './pages/dashboard/ReskillingPath';
import Chatbot from './pages/dashboard/Chatbot';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  // Using a soft redirect for the mock/hackathon prototype
  // In a real app we'd block if no token immediately.
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
            <Route index element={<Overview />} />
            <Route path="hiring-trends" element={<HiringTrends />} />
            <Route path="skills" element={<SkillsIntelligence />} />
            <Route path="vulnerability" element={<AIVulnerability />} />
            <Route path="worker" element={<WorkerIntelligence />} />
            <Route path="reskilling" element={<ReskillingPath />} />
            <Route path="chatbot" element={<Chatbot />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
