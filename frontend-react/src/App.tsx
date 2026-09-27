import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { PasswordGate } from './components/auth/PasswordGate';
import { NotificationsProvider } from './components/ui/Toasts';
import { router } from './routes';
import './styles/tokens.css';
import './styles/app.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NotificationsProvider>
        <PasswordGate>
          <RouterProvider router={router} />
        </PasswordGate>
      </NotificationsProvider>
    </QueryClientProvider>
  );
}
