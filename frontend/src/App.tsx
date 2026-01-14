import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from './store/authStore';
import { useTelegram } from './hooks/useTelegram';
import { authApi } from './api/auth';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/LoginPage';
import OverviewPage from './pages/OverviewPage';
import SalesPage from './pages/SalesPage';
import InventoryPage from './pages/InventoryPage';
import RecipesPage from './pages/RecipesPage';
import IngredientsPage from './pages/IngredientsPage';
import ButtonsPage from './pages/ButtonsPage';
import ExpensesPage from './pages/ExpensesPage';
import OwnerReportPage from './pages/OwnerReportPage';
import SettingsPage from './pages/SettingsPage';
import { ROUTES } from './utils/constants';

function App() {
  const { initAuth, isAuthenticated, isLoading, setToken, setUser } = useAuthStore();
  const { isReady, initData, user: tgUser } = useTelegram();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // Автоматическая авторизация при открытии из Telegram (для мобильных)
  useEffect(() => {
    if (!initData || isAuthenticated) return;
    
    // Проверяем, есть ли pending авторизация из браузера
    const authPending = localStorage.getItem('telegram_auth_pending');
    const startParam = new URLSearchParams(window.location.search).get('tgWebAppStartParam');
    
    // Если есть pending авторизация и startParam совпадает - это возврат из браузера
    if (authPending && startParam && startParam.includes('webauth_')) {
      console.log('Обнаружена авторизация из браузера, выполняем автовход...');
      
      // Выполняем авторизацию через Mini App endpoint
      authApi.loginWithTelegram(initData)
        .then((response) => {
          console.log('Авторизация успешна, возвращаем в браузер с токеном');
          
          // Формируем URL для возврата в браузер
          const browserUrl = `${window.location.origin}/login?token=${response.access_token}&user_id=${response.user.id}`;
          
          // Открываем браузер с токеном
          window.open(browserUrl, '_blank');
          
          // Показываем сообщение пользователю
          alert('Авторизация успешна! Вернитесь в браузер для продолжения работы.');
        })
        .catch((err) => {
          console.error('Ошибка авторизации:', err);
          alert('Ошибка авторизации. Попробуйте еще раз.');
        });
    }
  }, [initData, isAuthenticated, setToken, setUser]);

  // Show loading only while checking auth state, not while waiting for Telegram
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="Загрузка..." />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.LOGIN} element={<LoginPage />} />
        
        {isAuthenticated ? (
          <Route element={<AppLayout />}>
            <Route path={ROUTES.OVERVIEW} element={<OverviewPage />} />
            <Route path={ROUTES.SALES} element={<SalesPage />} />
            <Route path={ROUTES.INVENTORY} element={<InventoryPage />} />
            <Route path={ROUTES.RECIPES} element={<RecipesPage />} />
            <Route path={ROUTES.INGREDIENTS} element={<IngredientsPage />} />
            <Route path={ROUTES.BUTTONS} element={<ButtonsPage />} />
            <Route path={ROUTES.EXPENSES} element={<ExpensesPage />} />
            <Route path={ROUTES.OWNER_REPORT} element={<OwnerReportPage />} />
            <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
          </Route>
        ) : (
          <Route path="*" element={<Navigate to={ROUTES.LOGIN} replace />} />
        )}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
