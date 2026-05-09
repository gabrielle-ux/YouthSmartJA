<template>
  <header class="header">

    <!--make this navigate to home when clicked-->
    <RouterLink to="/" class="logo">
      <span class="logo-text">DriftDater</span>
    </RouterLink>

    <div class="buttons">
      <!-- SIGNUP -->
      <RouterLink 
        to="/signup" 
        class="nav-btn-filled"
        :class="{ active: route.path === '/signup' }"
      >
        Sign Up
      </RouterLink>

      <!-- LOGIN -->
      <RouterLink 
        to="/login" 
        class="nav-btn-outline"
        :class="{ active: route.path === '/login' }"
      >
        Login
      </RouterLink>
    </div>
  </header>
</template>

<script setup>
//import { RouterLink } from "vue-router";

import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const isLoggedIn = computed(() => {
  return !!localStorage.getItem("token");
});

const allowedRoutes = ["/", "/login", "/signup"];

const showHeader = computed(() => {
  return !isLoggedIn.value && allowedRoutes.includes(route.path);
});

</script>