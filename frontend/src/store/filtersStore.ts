import { create } from 'zustand';
import dayjs, { Dayjs } from 'dayjs';

interface FiltersState {
  dateRange: [Dayjs, Dayjs];
  locationId: number | null;
  terminalId: number | null;
  
  setDateRange: (range: [Dayjs, Dayjs]) => void;
  setLocationId: (id: number | null) => void;
  setTerminalId: (id: number | null) => void;
  resetFilters: () => void;
}

const getDefaultDateRange = (): [Dayjs, Dayjs] => {
  const end = dayjs();
  const start = dayjs().subtract(7, 'day');
  return [start, end];
};

export const useFiltersStore = create<FiltersState>((set) => ({
  dateRange: getDefaultDateRange(),
  locationId: null,
  terminalId: null,

  setDateRange: (range) => set({ dateRange: range }),
  setLocationId: (id) => set({ locationId: id, terminalId: null }), // Reset terminal when location changes
  setTerminalId: (id) => set({ terminalId: id }),
  
  resetFilters: () => set({
    dateRange: getDefaultDateRange(),
    locationId: null,
    terminalId: null,
  }),
}));
