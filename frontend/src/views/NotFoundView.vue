<template>
  <div class="not-found-container">
    <div class="glass-card not-found-card">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">페이지를 찾을 수 없습니다</h2>
      <p class="error-desc">
        요청하신 페이지가 사라졌거나 잘못된 주소입니다.<br/>
        입력하신 주소가 정확한지 다시 한번 확인해주세요.
      </p>
      <router-link to="/" class="btn-primary home-btn">
        홈으로 돌아가기
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px); /* header height subtraction */
  padding: 2rem;
}

.not-found-card {
  text-align: center;
  padding: 4rem 3rem;
  max-width: 500px;
  width: 100%;
}

.error-code {
  font-size: 6rem;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 1rem 0;
}

.error-desc {
  color: var(--text-light);
  line-height: 1.6;
  margin-bottom: 2rem;
}

.home-btn {
  display: inline-block;
  padding: 0.8rem 2rem;
  font-weight: 600;
  text-decoration: none;
}
</style>
