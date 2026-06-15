import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { WatchlistItem } from '@/lib/types'

interface WatchlistStore {
  items: WatchlistItem[]
  setItems: (items: WatchlistItem[]) => void
  addItem: (item: WatchlistItem) => void
  removeItem: (ticker: string) => void
  isInWatchlist: (ticker: string) => boolean
}

export const useWatchlistStore = create<WatchlistStore>()(
  persist(
    (set, get) => ({
      items: [],
      setItems: (items) => set({ items }),
      addItem: (item) =>
        set((state) => ({
          items: state.items.some((i) => i.company.ticker === item.company.ticker)
            ? state.items
            : [...state.items, item],
        })),
      removeItem: (ticker) =>
        set((state) => ({
          items: state.items.filter((i) => i.company.ticker !== ticker),
        })),
      isInWatchlist: (ticker) => get().items.some((i) => i.company.ticker === ticker),
    }),
    { name: 'watchlist-storage' }
  )
)
