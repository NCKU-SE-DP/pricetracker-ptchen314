import { defineStore } from 'pinia';
import axios from 'axios';
import Categories from '@/constants/categories';

export const usePricesStore = defineStore('prices', {
    state: () => {
        const initialState = {
            categories: {},
            isLoading: false,
            errorMessage: '',
            updatedTime: null
        };
        Object.keys(Categories).forEach(category => {
            initialState.categories[category] = [];
        });
        return initialState;
    },
    actions: {
        async fetchPrices() {
            this.isLoading = true;
            this.errorMessage = '';
            Object.keys(Categories).forEach(category => {
                this.categories[category] = [];
            });
            try {
                const response = await axios.get('http://localhost:8000/api/v1/prices/necessities-price');
                let data = response.data.data;

                data.forEach(item => {
                    const categoryKey = Object.keys(Categories).find(
                        key => Categories[key] === item.類別
                    );
                    if (categoryKey) {
                        this.categories[categoryKey].push(item);
                    }
                });
                this.updatedTime = new Date();
                this.updatedTime = this.updatedTime.toLocaleString('zh-TW', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                }).replace(/(\d{4})\/(\d{2})\/(\d{2}), (\d{2}):(\d{2}):(\d{2})/, "$1/$2/$3 $4:$5");
            } catch (error) {
                this.errorMessage = 'Error fetching prices: ' + error.message;
            } finally {
                this.isLoading = false;
            }
        },
    },
    getters: {
        getPricesByCategory: (state) => (category) => {
            return state.categories[category] || [];
        },
        getAllCategories: (state) => {
            return state.categories;
        },
        getProductList: (state) => (category) => {
            return state.categories[category].map(item => item.產品名稱);
        },
    }
});
