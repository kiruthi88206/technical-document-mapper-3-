import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import TerminologyPage from './pages/TerminologyPage';
import ConceptMapperPage from './pages/ConceptMapperPage';
import SearchPage from './pages/SearchPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = localStorage.getItem('techmapper_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    localStorage.removeItem('techmapper_token');
    localStorage.removeItem('techmapper_user');
    setCurrentUser(null);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Dedicated Login / Register Screen */}
        <Route
          path="/login"
          element={
            currentUser ? (
              <Navigate to="/" replace />
            ) : (
              <LoginPage onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        {/* Protected App Workspace */}
        <Route
          path="/*"
          element={
            !currentUser ? (
              <Navigate to="/login" replace />
            ) : (
              <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-800">
                {/* Main Application Sidebar */}
                <Sidebar user={currentUser} onLogout={handleLogout} />

                {/* Content Area with Navbar */}
                <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
                  <Navbar user={currentUser} />

                  <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50">
                    <Routes>
                      <Route path="/" element={<DashboardPage />} />
                      <Route path="/documents" element={<DocumentsPage />} />
                      <Route path="/documents/:id" element={<DocumentDetailPage />} />
                      <Route path="/terminology" element={<TerminologyPage />} />
                      <Route path="/mapper" element={<ConceptMapperPage />} />
                      <Route path="/search" element={<SearchPage />} />
                      <Route path="/settings" element={<SettingsPage />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </main>
                </div>
              </div>
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
