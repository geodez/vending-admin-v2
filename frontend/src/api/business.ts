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
export const getLocations = () => apiClient.get<Location[]>('/business/locations');
export const createLocation = (data: { name: string }) => 
  apiClient.post<Location>('/business/locations', data);
export const updateLocation = (id: number, data: { name: string }) =>
  apiClient.put<Location>(`/v1/business/locations/${id}`, data);
export const deleteLocation = (id: number) =>
  apiClient.delete(`/v1/business/locations/${id}`);

// Products
export const getProducts = () => apiClient.get<Product[]>('/business/products');
export const createProduct = (data: Partial<Product>) =>
  apiClient.post<Product>('/business/products', data);
export const updateProduct = (id: string, data: Partial<Product>) =>
  apiClient.put<Product>(`/v1/business/products/${id}`, data);
export const deleteProduct = (id: string) =>
  apiClient.delete(`/v1/business/products/${id}`);

// Ingredients
export const getIngredients = () => apiClient.get<Ingredient[]>('/business/ingredients');
export const createIngredient = (data: Partial<Ingredient>) =>
  apiClient.post<Ingredient>('/business/ingredients', data);
export const updateIngredient = (code: string, data: Partial<Ingredient>) =>
  apiClient.put<Ingredient>(`/v1/business/ingredients/${code}`, data);
export const deleteIngredient = (code: string) =>
  apiClient.delete(`/v1/business/ingredients/${code}`);

// Drinks (Recipes)
export const getDrinks = () => apiClient.get<Drink[]>('/business/drinks');
export const createDrink = (data: Partial<Drink>) =>
  apiClient.post<Drink>('/business/drinks', data);
export const updateDrink = (id: number, data: Partial<Drink>) =>
  apiClient.put<Drink>(`/v1/business/drinks/${id}`, data);
export const deleteDrink = (id: number) =>
  apiClient.delete(`/v1/business/drinks/${id}`);

// Recipes (drink items)
export const getRecipe = (drinkId: number) =>
  apiClient.get<Recipe>(`/v1/business/drinks/${drinkId}/recipe`);
export const updateRecipe = (drinkId: number, items: Array<{ ingredient_code: string; qty_per_unit: number; unit: string }>) =>
  apiClient.put(`/v1/business/drinks/${drinkId}/recipe`, { items });
