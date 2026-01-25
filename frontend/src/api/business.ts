/**
 * API module for business entities (locations, products, ingredients, drinks, recipes)
 */
import apiClient from './client';
import type {
  Location,
  Product,
  Ingredient,
  Drink,
  Recipe
} from '@/types/api';

// Locations
export const getLocations = () => apiClient.get<Location[]>('/locations');
export const createLocation = (data: { name: string }) => 
  apiClient.post<Location>('/business/locations', data);
export const updateLocation = (id: number, data: { name: string }) =>
  apiClient.put<Location>(`/business/locations/${id}`, data);
export const deleteLocation = (id: number) =>
  apiClient.delete(`/business/locations/${id}`);

// Products
export const getProducts = () => apiClient.get<Product[]>('/business/products');
export const createProduct = (data: Partial<Product>) =>
  apiClient.post<Product>('/business/products', data);
export const updateProduct = (id: string, data: Partial<Product>) =>
  apiClient.put<Product>(`/business/products/${id}`, data);
export const deleteProduct = (id: string) =>
  apiClient.delete(`/business/products/${id}`);

// Ingredients
export const getIngredients = () => apiClient.get<Ingredient[]>('/ingredients');
export const createIngredient = (data: Partial<Ingredient>) =>
  apiClient.post<Ingredient>('/ingredients', data);
export const updateIngredient = (code: string, data: Partial<Ingredient>) =>
  apiClient.put<Ingredient>(`/ingredients/${code}`, data);
export const bulkUpdateIngredients = (codes: string[], data: Partial<Ingredient>) =>
  apiClient.put<{ updated: number; total: number; errors?: string[] }>('/ingredients/bulk/update', {
    ingredient_codes: codes,
    ...data
  });
export const deleteIngredient = (code: string) =>
  apiClient.delete(`/ingredients/${code}`);

// Drinks (Recipes)
export const getDrinks = () => apiClient.get<Drink[]>('/business/drinks');
export const createDrink = (data: Partial<Drink>) =>
  apiClient.post<Drink>('/business/drinks', data);
export const updateDrink = (id: number, data: Partial<Drink>) =>
  apiClient.put<Drink>(`/business/drinks/${id}`, data);
export const deleteDrink = (id: number) =>
  apiClient.delete(`/business/drinks/${id}`);

// Recipes (drink items)
export const getRecipe = (drinkId: number) =>
  apiClient.get<Recipe>(`/business/drinks/${drinkId}/recipe`);
export const updateRecipe = (drinkId: number, items: Array<{ ingredient_code: string; qty_per_unit: number; unit: string }>) =>
  apiClient.put(`/business/drinks/${drinkId}/recipe`, { items });
