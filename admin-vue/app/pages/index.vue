<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-logo">
        <img src="/kbds_logo.svg" alt="KBDS" class="login-logo-img" />
      </div>
      <h2 class="login-title">시스템 로그인</h2>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">아이디</label>
          <input
            v-model="username"
            type="text"
            class="form-input"
            placeholder="admin"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label class="form-label">비밀번호</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="비밀번호를 입력하세요"
            autocomplete="current-password"
          />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="btn btn-primary btn-full login-btn">
          로그인
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "auth", middleware: "auth" });

const router = useRouter();
const loggedIn = useCookie("kb_logged_in", { maxAge: 60 * 60 * 24 * 7 });

const username = ref("");
const password = ref("");
const errorMsg = ref("");

function handleLogin() {
  errorMsg.value = "";
  if (username.value === "admin" && password.value === "kbdata1!") {
    loggedIn.value = "true";
    router.push("/dashboard");
  } else {
    errorMsg.value = "아이디 또는 비밀번호가 일치하지 않습니다.";
  }
}
</script>

<style scoped>
.login-wrapper {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 40px 36px 36px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.login-logo-img {
  max-width: 160px;
  max-height: 50px;
  object-fit: contain;
}

.login-title {
  font-weight: 700;
  font-family: "KBFGDisplay";
  font-size: 20px;
  text-align: center;
  color: #222;
  margin-bottom: 24px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.error-msg {
  color: #d32f2f;
  font-size: 13px;
  margin-bottom: 12px;
  text-align: center;
}

.login-btn {
  margin-top: 8px;
  padding: 11px;
  font-size: 15px;
  font-weight: 600;
}
</style>
