import { CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { ApiKeysProvider } from './components/apiKeys/ApiKeysProvider';
import { NotificationsProvider } from './components/common/Notifications';
import { router } from './routes';
import { theme } from './theme';

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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <NotificationsProvider>
          <ApiKeysProvider>
            <RouterProvider router={router} />
          </ApiKeysProvider>
        </NotificationsProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
