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
          <div class="input-icon-wrap">
            <Icon name="lucide:user" class="input-icon" />
            <input
              v-model="username"
              type="text"
              class="form-input has-icon"
              placeholder="admin"
              autocomplete="username"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">비밀번호</label>
          <div class="input-icon-wrap">
            <Icon name="lucide:lock" class="input-icon" />
            <input
              v-model="password"
              type="password"
              class="form-input has-icon"
              placeholder="비밀번호를 입력하세요"
              autocomplete="current-password"
            />
          </div>
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
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 44px 40px 40px;
  width: 100%;
  max-width: 420px;
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.15),
    0 1px 3px rgba(0, 0, 0, 0.05);
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  color: #1e293b;
  margin-bottom: 28px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px 10px 38px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s ease;
}

.form-input:focus {
  background: #fff;
  border-color: var(--kb-yellow);
  box-shadow: 0 0 0 3px rgba(255, 188, 0, 0.2);
}

.input-icon-wrap {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: #94a3b8;
  pointer-events: none;
}

.error-msg {
  color: #d32f2f;
  font-size: 13px;
  margin-bottom: 12px;
  text-align: center;
}

.login-btn {
  margin-top: 10px;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(255, 188, 0, 0.25);
  transition: all 0.2s ease;
}
</style>
