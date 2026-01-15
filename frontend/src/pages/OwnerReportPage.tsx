import { useEffect, useState } from 'react';
import { Spin, Result, Button, Typography } from 'antd';
import apiClient from '../api/client';

const { Paragraph } = Typography;

type LoadState =
  | { kind: 'loading' }
  | { kind: 'forbidden' }
  | { kind: 'unauthorized' }
  | { kind: 'error'; message?: string }
  | { kind: 'ok'; data: any };

export default function OwnerReportPage() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        const res = await apiClient.get('/analytics/owner-report');
        if (!alive) return;
        setState({ kind: 'ok', data: res.data });
      } catch (e: any) {
        if (!alive) return;
        const status = e?.response?.status;

        if (status === 401) {
          setState({ kind: 'unauthorized' });
          window.location.href = '/login';
          return;
        }
        if (status === 403) {
          setState({ kind: 'forbidden' });
          return;
        }
        setState({ kind: 'error', message: e?.message });
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  if (state.kind === 'loading') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (state.kind === 'forbidden') {
    return (
      <Result
        status="403"
        title="Доступ запрещен"
        subTitle="Отчёт собственника доступен только роли owner."
        extra={[
          <Button key="overview" type="primary" onClick={() => (window.location.href = '/overview')}>
            В обзор
          </Button>,
        ]}
      />
    );
  }

  if (state.kind === 'error') {
    return (
      <Result
        status="error"
        title="Ошибка загрузки"
        subTitle={state.message || 'Не удалось получить данные отчёта.'}
        extra={[
          <Button key="retry" type="primary" onClick={() => window.location.reload()}>
            Повторить
          </Button>,
        ]}
      />
    );
  }

  if (state.kind === 'ok') {
    return (
      <div style={{ padding: 24 }}>
        <Paragraph strong>Owner report (MVP):</Paragraph>
        <pre
          style={{
            background: '#0b1220',
            color: '#e6edf3',
            padding: 16,
            borderRadius: 8,
            overflow: 'auto',
          }}
        >
          {JSON.stringify(state.data, null, 2)}
        </pre>
      </div>
    );
  }

  return null;
}
