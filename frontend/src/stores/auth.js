import { defineStore } from 'pinia';
import axios from 'axios';
import router from '../router';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        accessToken: null,
        isLoading: false,
        errorMessage: '',
    }),
    actions: {
        async register(username, password) {
            this.isLoading = true;
            try {
                await axios.post('http://localhost:8000/api/v1/users/register', {
                    username: username,
                    password: password,
                },
                );
                await this.login(username, password);
            } catch (error) {
                this.errorMessage = error.response?.data.detail || 'Failed to register';
            } finally {
                this.isLoading = false;
            }
        },
        async login(username, password) {
            this.isLoading = true;
            try {
                const response = await axios.post('http://localhost:8000/api/v1/users/login', {
                    username: username,
                    password: password,
                },
                { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
                );
                this.accessToken = response.data.data.access_token;
                localStorage.setItem('accessToken', this.accessToken);
                axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`;
                await this.fetchUser();
                router.push({ name: 'PriceOverview' });
            } catch (error) {
                this.errorMessage = error.response?.data.detail || 'Failed to login';
            } finally {
                this.isLoading = false;
            }
        },
        logout() {
            this.user = null;
            this.accessToken = null;
            localStorage.removeItem('accessToken');
            delete axios.defaults.headers.common['Authorization'];
            router.push({ name: 'PriceOverview' });

        },
        async fetchUser() {
            try {
                const response = await axios.get('http://localhost:8000/api/v1/users/me');
                this.user = response.data.data.username;
                this.errorMessage = '';
            } catch (error) {
                this.logout();
            }
        },
        initializeFromLocalStorage() {
            const token = localStorage.getItem('accessToken');
            if (token) {
                this.accessToken = token;
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                this.fetchUser();
            }
        }
    },
    getters: {
        isLoggedIn: (state) => !!state.accessToken,
        getUserName: (state) => state.user,
        getLoginError: (state) => state.errorMessage,
    }
});
