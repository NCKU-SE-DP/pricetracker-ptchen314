import { defineStore } from 'pinia';
import axios from 'axios';
import { useAuthStore } from './auth';

export const useNewsStore = defineStore('news', {
    state: () => ({
        newsList: [],
        isLoading: false,
        errorMessage: '',
    }),
    actions: {
        async fetchNews() {
            this.isLoading = true;
            this.errorMessage = '';
            const authStore = useAuthStore();
            const apiUrl = authStore.isLoggedIn 
                ? 'http://localhost:8000/api/v1/news/user_news'
                : 'http://localhost:8000/api/v1/news/news';
            try {
                const response = await axios.get(apiUrl,
                    { headers: authStore.isLoggedIn ? { Authorization: `Bearer ${authStore.accessToken}` } : {}
                });
                this.newsList = response.data.data.map(news => ({ ...news, isSummaryLoading: false }));
            } catch (error) {
                this.errorMessage = 'Error fetching news: ' + error.message;
            } finally {
                this.isLoading = false;
            }
        },
        async promptSearchNews(prompt) {
            if(this.isLoading) return;
            this.isLoading = true;
            this.errorMessage = '';
            try {
                const response = await axios.post('http://localhost:8000/api/v1/news/search_news', {prompt: prompt});
                this.newsList = response.data.data.map(news => ({ ...news, isSummaryLoading: false }));
            } catch (error) {
                this.errorMessage = 'Error fetching news: ' + error.message;
            } finally {
                this.isLoading = false;
            }            
        },
        async fetchNewsSummary(content, index) {
            if(this.newsList[index].isSummaryLoading) return;
            this.newsList[index].isSummaryLoading = true;
            this.errorMessage = '';
            try {
                const response = await axios.post('http://localhost:8000/api/v1/news/news_summary', {content: content});
                if (response.data.data && index >= 0 && index < this.newsList.length) {
                    this.newsList[index].reason = response.data.data.reason;
                    this.newsList[index].summary = response.data.data.summary;
                }
            } catch (error) {
                this.errorMessage = 'Error fetching news: ' + error.message;
            } finally {
                this.newsList[index].isSummaryLoading = false;
            }
        },
        async toggleUpvote(newsId) {
            const index = this.newsList.findIndex(news => news.id === newsId);
            if (index === -1) {
                console.error("News not found");
                return;
            }
            const currentUpvotes = this.newsList[index].upvotes;
            const currentIsUpvoted = this.newsList[index].is_upvoted;
        
            if (this.newsList[index].is_upvoted) {
                this.newsList[index].upvotes--;
            } else {
                this.newsList[index].upvotes++;
            }
            this.newsList[index].is_upvoted = !this.newsList[index].is_upvoted;
        
            try {
                await axios.post(`http://localhost:8000/api/v1/news/${newsId}/upvote`);
            } catch (error) {
                console.error("Error toggling upvote: ", error);
                this.errorMessage = 'Error toggling upvote: ' + error.message;
                //roll back if failed
                this.newsList[index].upvotes = currentUpvotes;
                this.newsList[index].is_upvoted = currentIsUpvoted;
            }
        }

    },
    getters: {
        getNews: (state) => {
            return state.newsList;
        },
    },
});