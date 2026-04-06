import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import CompetencyModel from './components/CompetencyModel';
import AssessmentMatrix from './components/AssessmentMatrix';
import QuestionBook from './components/QuestionBook';
import UploadRecords from './components/UploadRecords';
import ReportGeneration from './components/ReportGeneration';
import JudgeManual from './components/JudgeManual';
import Login from './components/Login';
import UserSettings from './components/UserSettings';
import PracticeList from './components/PracticeList';
import PracticeSession from './components/PracticeSession';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [navigationStack, setNavigationStack] = useState<string[]>(['dashboard']);
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return !!sessionStorage.getItem('auth_token');
  });
  const [showUserMenu, setShowUserMenu] = useState(false);

  const navigateTo = (page: string) => {
    setCurrentPage(page);
    setNavigationStack([...navigationStack, page]);
    setShowUserMenu(false);
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
      case 'judge-manual':
        return <JudgeManual onBack={goBack} />;
      case 'upload':
        return <UploadRecords onBack={goBack} />;
      case 'report':
        return <ReportGeneration onBack={goBack} onNavigate={navigateTo} />;
      case 'practice':
        return <PracticeList onBack={goBack} onNavigate={navigateTo} />;
      case 'practice-session':
        return <PracticeSession onBack={goBack} />;
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

  return <div className="min-h-screen">{renderPage()}</div>;
}
