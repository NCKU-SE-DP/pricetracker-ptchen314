<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
        <div class="menu-icon" @click="toggleMenu" v-if="isMobile">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <ul class="options" :class="{ 'mobile-menu': isMobile, 'hidden': !showMenu }">
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
    </nav>
</template>

<script>
import { useAuthStore } from '@/stores/auth';
import { ref, onMounted, onUnmounted, computed } from 'vue';

export default {
    name: 'NavBar',
    setup() {
        const isMobile = ref(false);
        const showMenu = ref(true);

        const checkMobile = () => {
            isMobile.value = window.innerWidth <= 768;
            showMenu.value = !isMobile.value;
        };

        const toggleMenu = () => {
            showMenu.value = !showMenu.value;
        };

        onMounted(() => {
            checkMobile();
            window.addEventListener('resize', checkMobile);
        });

        onUnmounted(() => {
            window.removeEventListener('resize', checkMobile);
        });

        const authStore = useAuthStore();

        const isLoggedIn = computed(() => authStore.isLoggedIn);
        const getUserName = computed(() => authStore.getUserName);

        const logout = () => {
            authStore.logout();
        };

        return {
            isMobile,
            showMenu,
            toggleMenu,
            isLoggedIn,
            getUserName,
            logout
        };
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
    align-items: center;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

.menu-icon {
    display: none;
    flex-direction: column;
    cursor: pointer;
}

.menu-icon span {
    height: 3px;
    width: 25px;
    background-color: #575B5D;
    margin: 3px 0;
}

@media (max-width: 768px) {
    .menu-icon {
        display: flex;
    }

    .options {
        flex-direction: column;
        position: absolute;
        top: 4.5em;
        left: 0;
        width: 100%;
        background-color: #f3f3f3;
        padding: 1em;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    .options.hidden {
        display: none;
    }

    .navbar li {
        margin: 0.5em 0;
        width: 100%;
        text-align: center;
    }

    .navbar ul {
        width: 100%;
    }
}

@media (min-width: 769px) {
    .options {
        display: flex !important;
    }
}
</style>