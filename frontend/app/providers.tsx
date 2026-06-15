'use client'
import { QueryClientProvider as TanstackProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/query-client'

export function QueryClientProvider({ children }: { children: React.ReactNode }) {
  return (
    <TanstackProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </TanstackProvider>
  )
}
