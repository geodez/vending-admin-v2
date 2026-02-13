# 🚀 План разработки Vending Admin v2

**Дата начала:** 12.01.2026  
**Предполагаемая длительность:** 5-6 недель  
**Команда:** 1-2 разработчика

---

## 📋 Общий timeline

| Этап | Длительность | Статус |
|------|--------------|--------|
| 1. Инфраструктура и Auth | 1 неделя | 🟡 В процессе |
| 2. Синхронизация Vendista | 3-4 дня | ⏳ Ожидание |
| 3. CRUD сущностей | 1 неделя | ⏳ Ожидание |
| 4. Склад и загрузки | 3-4 дня | ⏳ Ожидание |
| 5. Продажи и KPI | 1 неделя | ⏳ Ожидание |
| 6. Переменные расходы | 2-3 дня | ⏳ Ожидание |
| 7. Отчет собственника | 3-4 дня | ⏳ Ожидание |
| 8. Настройки | 2-3 дня | ⏳ Ожидание |
| 9. Тестирование и деплой | 1 неделя | ⏳ Ожидание |

---

## 🏗️ Этап 1: Инфраструктура и аутентификация (1 неделя)

### Задачи Backend

#### 1.1. Базовая структура проекта (Day 1)
- [ ] Создать структуру директорий
  ```bash
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── api/
  │   ├── auth/
  │   ├── models/
  │   ├── schemas/
  │   ├── crud/
  │   └── db/
  ├── migrations/
  ├── tests/
  ├── requirements.txt
  ├── Dockerfile
  └── docker-compose.yml
  ```

- [ ] Настроить `requirements.txt`:
  ```
  fastapi==0.109.0
  uvicorn[standard]==0.27.0
  sqlalchemy==2.0.25
  alembic==1.13.1
  psycopg2-binary==2.9.9
  pydantic-settings==2.1.0
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  httpx==0.26.0
  python-multipart==0.0.6
  ```

- [ ] Создать `docker-compose.yml`:
  ```yaml
  version: '3.8'
  services:
    db:
      image: postgres:16
      environment:
        POSTGRES_DB: vending
        POSTGRES_USER: vending
        POSTGRES_PASSWORD: vending_pass
      ports:
        - "5432:5432"
      volumes:
        - db_data:/var/lib/postgresql/data
    
    app:
      build: .
      command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      volumes:
        - .:/app
      ports:
        - "8000:8000"
      depends_on:
        - db
      environment:
        DATABASE_URL: postgresql://vending:vending_pass@db:5432/vending
        SECRET_KEY: your-secret-key-here
        TELEGRAM_BOT_TOKEN: your-bot-token
  
  volumes:
    db_data:
  ```

- [ ] Создать `Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  
  WORKDIR /app
  
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  COPY . .
  
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

#### 1.2. Database и Models (Day 1-2)

- [ ] Настроить SQLAlchemy (`app/db/session.py`):
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  from app.config import settings
  
  engine = create_engine(settings.DATABASE_URL)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  Base = declarative_base()
  
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

- [ ] Создать модель `User` (`app/models/user.py`):
  ```python
  from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime
  from sqlalchemy.sql import func
  from app.db.session import Base
  
  class User(Base):
      __tablename__ = "users"
      
      id = Column(Integer, primary_key=True, index=True)
      telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
      username = Column(String, nullable=True)
      first_name = Column(String, nullable=True)
      last_name = Column(String, nullable=True)
      role = Column(String, nullable=False, default="operator")  # owner, operator
      is_active = Column(Boolean, nullable=False, default=True)
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
  ```

- [ ] Создать Alembic миграцию для `users`:
  ```bash
  alembic init migrations
  alembic revision --autogenerate -m "create users table"
  alembic upgrade head
  ```

#### 1.3. Telegram Auth (Day 2-3)

- [ ] Создать `app/auth/telegram.py`:
  ```python
  import hashlib
  import hmac
  from urllib.parse import parse_qs
  from datetime import datetime, timedelta
  from app.config import settings
  
  def validate_telegram_auth(init_data: str) -> dict:
      """
      Валидация initData от Telegram WebApp.
      Возвращает dict с данными пользователя или None.
      """
      try:
          data_dict = parse_qs(init_data)
          hash_value = data_dict.get('hash', [None])[0]
          
          if not hash_value:
              return None
          
          # Собираем все параметры кроме hash
          check_string = '\n'.join([
              f"{k}={v[0]}" for k, v in sorted(data_dict.items())
              if k != 'hash'
          ])
          
          # Вычисляем secret_key
          secret_key = hmac.new(
              b"WebAppData",
              settings.TELEGRAM_BOT_TOKEN.encode(),
              hashlib.sha256
          ).digest()
          
          # Вычисляем hash
          calculated_hash = hmac.new(
              secret_key,
              check_string.encode(),
              hashlib.sha256
          ).hexdigest()
          
          # Проверяем hash
          if calculated_hash != hash_value:
              return None
          
          # Проверяем auth_date (не старше 24 часов)
          auth_date_str = data_dict.get('auth_date', [None])[0]
          if not auth_date_str:
              return None
          
          auth_date = datetime.fromtimestamp(int(auth_date_str))
          if datetime.now() - auth_date > timedelta(hours=24):
              return None
          
          # Парсим данные пользователя
          import json
          user_data = json.loads(data_dict.get('user', ['{}'])[0])
          
          return {
              'user_id': user_data.get('id'),
              'username': user_data.get('username'),
              'first_name': user_data.get('first_name'),
              'last_name': user_data.get('last_name'),
          }
      except Exception:
          return None
  ```

- [ ] Создать `app/auth/jwt.py`:
  ```python
  from datetime import datetime, timedelta
  from jose import JWTError, jwt
  from app.config import settings
  
  def create_access_token(data: dict, expires_delta: timedelta = None):
      to_encode = data.copy()
      if expires_delta:
          expire = datetime.utcnow() + expires_delta
      else:
          expire = datetime.utcnow() + timedelta(days=7)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
      return encoded_jwt
  
  def verify_token(token: str):
      try:
          payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
          return payload
      except JWTError:
          return None
  ```

- [ ] Создать endpoint `/api/v1/auth/telegram`:
  ```python
  # app/api/v1/auth.py
  from fastapi import APIRouter, Depends, HTTPException
  from sqlalchemy.orm import Session
  from app.db.session import get_db
  from app.auth.telegram import validate_telegram_auth
  from app.auth.jwt import create_access_token
  from app.models.user import User
  from app.schemas.auth import TelegramAuthRequest, TokenResponse
  
  router = APIRouter()
  
  @router.post("/telegram", response_model=TokenResponse)
  def authenticate_telegram(request: TelegramAuthRequest, db: Session = Depends(get_db)):
      # Валидация initData
      user_data = validate_telegram_auth(request.init_data)
      if not user_data:
          raise HTTPException(status_code=401, detail="Invalid Telegram auth")
      
      # Поиск пользователя в БД
      user = db.query(User).filter(User.telegram_user_id == user_data['user_id']).first()
      
      if not user:
          raise HTTPException(status_code=403, detail="User not registered")
      
      if not user.is_active:
          raise HTTPException(status_code=403, detail="User is inactive")
      
      # Генерация JWT токена
      token = create_access_token(
          data={
              "user_id": user.id,
              "telegram_user_id": user.telegram_user_id,
              "role": user.role
          }
      )
      
      return TokenResponse(
          access_token=token,
          token_type="bearer",
          user={
              "id": user.id,
              "telegram_user_id": user.telegram_user_id,
              "username": user.username,
              "first_name": user.first_name,
              "role": user.role
          }
      )
  ```

#### 1.4. Auth Dependency (Day 3)

- [ ] Создать `app/api/deps.py`:
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
  from sqlalchemy.orm import Session
  from app.db.session import get_db
  from app.auth.jwt import verify_token
  from app.models.user import User
  
  security = HTTPBearer()
  
  def get_current_user(
      credentials: HTTPAuthorizationCredentials = Depends(security),
      db: Session = Depends(get_db)
  ) -> User:
      token = credentials.credentials
      payload = verify_token(token)
      
      if not payload:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid token"
          )
      
      user = db.query(User).filter(User.id == payload['user_id']).first()
      
      if not user or not user.is_active:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="User not found or inactive"
          )
      
      return user
  
  def require_owner(current_user: User = Depends(get_current_user)) -> User:
      if current_user.role != "owner":
          raise HTTPException(
              status_code=status.HTTP_403_FORBIDDEN,
              detail="Only owners can access this resource"
          )
      return current_user
  ```

### Задачи Frontend

#### 1.5. Базовая структура проекта (Day 3-4)

- [ ] Создать React + TypeScript проект с Vite:
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install
  ```

- [ ] Установить зависимости:
  ```bash
  npm install react-router-dom axios zustand antd recharts
  npm install @twa-dev/sdk
  npm install @types/node --save-dev
  ```

- [ ] Создать структуру:
  ```
  frontend/
  ├── src/
  │   ├── api/
  │   ├── components/
  │   ├── pages/
  │   ├── store/
  │   ├── hooks/
  │   ├── types/
  │   ├── utils/
  │   ├── App.tsx
  │   └── main.tsx
  ├── public/
  ├── index.html
  ├── vite.config.ts
  └── tsconfig.json
  ```

#### 1.6. Telegram SDK интеграция (Day 4)

- [ ] Создать `src/hooks/useTelegram.ts`:
  ```typescript
  import { useEffect, useState } from 'react';
  import WebApp from '@twa-dev/sdk';
  
  export const useTelegram = () => {
    const [user, setUser] = useState(WebApp.initDataUnsafe.user);
    const [initData, setInitData] = useState(WebApp.initData);
    
    useEffect(() => {
      WebApp.ready();
      WebApp.expand();
      
      // Настройка темы
      if (WebApp.colorScheme === 'dark') {
        document.documentElement.classList.add('dark');
      }
    }, []);
    
    return {
      user,
      initData,
      colorScheme: WebApp.colorScheme,
      themeParams: WebApp.themeParams,
      close: () => WebApp.close(),
      showAlert: (message: string) => WebApp.showAlert(message),
    };
  };
  ```

#### 1.7. API Client (Day 4)

- [ ] Создать `src/api/client.ts`:
  ```typescript
  import axios from 'axios';
  
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
  
  export const apiClient = axios.create({
    baseURL: API_BASE_URL,
  });
  
  // Interceptor для добавления токена
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  
  // Interceptor для обработки 401 ошибок
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
  ```

- [ ] Создать `src/api/auth.ts`:
  ```typescript
  import { apiClient } from './client';
  
  export const authApi = {
    authenticateTelegram: async (initData: string) => {
      const response = await apiClient.post('/auth/telegram', { init_data: initData });
      return response.data;
    },
    
    getMe: async () => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    },
  };
  ```

#### 1.8. Auth Store (Day 5)

- [ ] Создать `src/store/authStore.ts`:
  ```typescript
  import { create } from 'zustand';
  import { authApi } from '../api/auth';
  
  interface User {
    id: number;
    telegram_user_id: number;
    username?: string;
    first_name?: string;
    role: 'owner' | 'operator';
  }
  
  interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (initData: string) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
  }
  
  export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: localStorage.getItem('access_token'),
    isLoading: false,
    
    login: async (initData: string) => {
      set({ isLoading: true });
      try {
        const data = await authApi.authenticateTelegram(initData);
        localStorage.setItem('access_token', data.access_token);
        set({ user: data.user, token: data.access_token, isLoading: false });
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },
    
    logout: () => {
      localStorage.removeItem('access_token');
      set({ user: null, token: null });
    },
    
    checkAuth: async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      
      try {
        const user = await authApi.getMe();
        set({ user, token });
      } catch (error) {
        localStorage.removeItem('access_token');
        set({ user: null, token: null });
      }
    },
  }));
  ```

#### 1.9. Login Page (Day 5)

- [ ] Создать `src/pages/LoginPage.tsx`:
  ```typescript
  import React, { useEffect } from 'react';
  import { useNavigate } from 'react-router-dom';
  import { Button, Spin, Alert } from 'antd';
  import { useTelegram } from '../hooks/useTelegram';
  import { useAuthStore } from '../store/authStore';
  
  export const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { initData } = useTelegram();
    const { login, isLoading } = useAuthStore();
    const [error, setError] = React.useState<string | null>(null);
    
    useEffect(() => {
      // Автоматический вход при наличии initData
      if (initData) {
        handleLogin();
      }
    }, []);
    
    const handleLogin = async () => {
      try {
        setError(null);
        await login(initData);
        navigate('/');
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка аутентификации');
      }
    };
    
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h1>Вход в админ-панель</h1>
        {isLoading && <Spin size="large" />}
        {error && <Alert type="error" message={error} style={{ marginBottom: '20px' }} />}
        {!isLoading && !error && (
          <Button type="primary" onClick={handleLogin}>
            Войти через Telegram
          </Button>
        )}
      </div>
    );
  };
  ```

#### 1.10. Protected Route (Day 5)

- [ ] Создать `src/components/ProtectedRoute.tsx`:
  ```typescript
  import React, { useEffect } from 'react';
  import { Navigate } from 'react-router-dom';
  import { useAuthStore } from '../store/authStore';
  import { Spin } from 'antd';
  
  interface ProtectedRouteProps {
    children: React.ReactNode;
    requiredRole?: 'owner' | 'operator';
  }
  
  export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    children,
    requiredRole,
  }) => {
    const { user, token, checkAuth } = useAuthStore();
    const [isChecking, setIsChecking] = React.useState(true);
    
    useEffect(() => {
      const check = async () => {
        await checkAuth();
        setIsChecking(false);
      };
      check();
    }, []);
    
    if (isChecking) {
      return <Spin size="large" />;
    }
    
    if (!token || !user) {
      return <Navigate to="/login" replace />;
    }
    
    if (requiredRole && user.role !== requiredRole) {
      return <Navigate to="/" replace />;
    }
    
    return <>{children}</>;
  };
  ```

#### 1.11. App Routes (Day 5)

- [ ] Создать `src/App.tsx`:
  ```typescript
  import React from 'react';
  import { BrowserRouter, Routes, Route } from 'react-router-dom';
  import { ConfigProvider, theme } from 'antd';
  import { useTelegram } from './hooks/useTelegram';
  import { LoginPage } from './pages/LoginPage';
  import { ProtectedRoute } from './components/ProtectedRoute';
  import { OverviewPage } from './pages/OverviewPage';
  
  const App: React.FC = () => {
    const { colorScheme } = useTelegram();
    
    return (
      <ConfigProvider
        theme={{
          algorithm: colorScheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        }}
      >
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <OverviewPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    );
  };
  
  export default App;
  ```

### Критерии завершения Этапа 1

✅ Backend:
- [x] FastAPI работает на порту 8000
- [x] PostgreSQL подключена и работает
- [x] Миграция `users` применена
- [x] Endpoint `/api/v1/auth/telegram` работает
- [x] JWT токены генерируются и валидируются
- [x] Middleware для проверки токена работает

✅ Frontend:
- [x] React app работает на порту 5173
- [x] Telegram WebApp SDK интегрирован
- [x] Login page работает (аутентификация через Telegram)
- [x] Protected routes защищены
- [x] Auth store сохраняет токен

✅ Integration:
- [x] Frontend может аутентифицироваться через Backend
- [x] JWT токен сохраняется и используется для API запросов
- [x] Роли Owner и Operator различаются

---

## 📊 Следующие этапы (краткое описание)

### Этап 2: Синхронизация Vendista (3-4 дня)
- Перенос логики синхронизации из старого проекта
- Создание моделей `vendista_terminals`, `vendista_tx_raw`, `sync_state`
- Автоматическая синхронизация через cron

### Этап 3: CRUD сущностей (1 неделя)
- Модели: `locations`, `products`, `ingredients`, `drinks`, `recipes`
- CRUD API endpoints
- UI: Ингредиенты, Рецепты, Кнопки терминала

### Этап 4: Склад (3-4 дня)
- Модель `ingredient_loads`
- Представления: остатки, расход, алерты
- UI: 3 вкладки склада

### Этап 5: Продажи и KPI (1 неделя)
- Представления: `vw_tx_cogs`, `vw_kpi_daily`, `vw_kpi_product`
- UI: Обзор, Продажи с графиками

### Этап 6: Переменные расходы (2-3 дня)
- Модель `variable_expenses`
- UI: список + форма + аналитика

### Этап 7: Отчет собственника (3-4 дня)
- Представление `vw_owner_report_daily`
- UI: KPI + таблицы + "Что сделать"

### Этап 8: Настройки (2-3 дня)
- UI: управление пользователями, категории, маппинг

### Этап 9: Тестирование и деплой (1 неделя)
- Unit tests
- E2E tests
- CI/CD
- Production деплой

---

**Текущий прогресс:** Этап 1 в процессе (40%)  
**Следующая задача:** Завершить Backend auth endpoints
