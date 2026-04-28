import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import CompetencyModel from './components/CompetencyModel';
import AssessmentMatrix from './components/AssessmentMatrix';
import QuestionBook from './components/QuestionBook';
import ReportGeneration from './components/ReportGeneration';
import Login from './components/Login';
import UserSettings from './components/UserSettings';
import { Toaster } from 'sonner';

type Page = 'login' | 'dashboard' | 'competency' | 'matrix' | 'question' | 'report' | 'settings';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [navigationStack, setNavigationStack] = useState<Page[]>(['dashboard']);
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return !!sessionStorage.getItem('auth_token');
  });
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash && hash !== currentPage) {
        const validPage = hash as Page;
        if (['login', 'dashboard', 'competency', 'matrix', 'question', 'report', 'settings'].includes(validPage)) {
          setCurrentPage(validPage);
          setNavigationStack([...navigationStack, validPage]);
        }
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [currentPage, navigationStack]);

  const navigateTo = (page: string) => {
    const validPage = page as Page;
    if (validPage) {
      setCurrentPage(validPage);
      setNavigationStack([...navigationStack, validPage]);
      setShowUserMenu(false);
    }
  };

  const goBack = () => {
    const newStack = [...navigationStack];
    newStack.pop();
    const previousPage = newStack[newStack.length - 1] || 'dashboard';
    setCurrentPage(previousPage);
    setNavigationStack(newStack);
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    setCurrentPage('dashboard');
    setNavigationStack(['dashboard']);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentPage('login');
    setNavigationStack(['login']);
    setShowUserMenu(false);
  };

  const renderPage = () => {
    if (!isLoggedIn && currentPage !== 'login') {
      setCurrentPage('login');
    }

    switch (currentPage) {
      case 'login':
        return <Login onBack={goBack} onLogin={handleLogin} />;
      case 'settings':
        return <UserSettings onBack={goBack} onLogout={handleLogout} />;
      case 'dashboard':
        return (
          <Dashboard
            onNavigate={navigateTo}
            onUserClick={() => navigateTo('settings')}
            isLoggedIn={isLoggedIn}
          />
        );
      case 'competency':
        return <CompetencyModel onBack={goBack} />;
      case 'matrix':
        return <AssessmentMatrix onBack={goBack} />;
      case 'question':
        return <QuestionBook onBack={goBack} onNavigate={navigateTo} />;
      case 'report':
        return <ReportGeneration onBack={goBack} onNavigate={navigateTo} />;
      default:
        return (
          <Dashboard
            onNavigate={navigateTo}
            onUserClick={() => navigateTo('settings')}
            isLoggedIn={isLoggedIn}
          />
        );
    }
  };

  return (
    <div className="min-h-screen">
      {renderPage()}
      <Toaster position="top-center" richColors />
    </div>
  );
}