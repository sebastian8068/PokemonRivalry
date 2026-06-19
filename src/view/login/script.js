(function() {
  const tabLogin = document.getElementById('tabLoginBtn');
  const tabSignup = document.getElementById('tabSignupBtn');
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');

  function setActiveTab(active) {
    if (active === 'login') {
      tabLogin.classList.add('active');
      tabSignup.classList.remove('active');
      loginForm.classList.remove('hidden');
      signupForm.classList.add('hidden');
    } else {
      tabSignup.classList.add('active');
      tabLogin.classList.remove('active');
      signupForm.classList.remove('hidden');
      loginForm.classList.add('hidden');
    }
  }

  tabLogin.addEventListener('click', (e) => {
    e.preventDefault();
    setActiveTab('login');
  });
  tabSignup.addEventListener('click', (e) => {
    e.preventDefault();
    setActiveTab('signup');
  });

  function showError(inputEl, message) {
    const originalPlaceholder = inputEl.placeholder;
    inputEl.style.borderColor = '#BF616A';
    inputEl.style.background = '#3B2E38';
    inputEl.placeholder = message;
    setTimeout(() => {
      inputEl.style.borderColor = '#434C5E';
      inputEl.style.background = '#3B4252';
    }, 600);
    setTimeout(() => { inputEl.placeholder = originalPlaceholder; }, 1200);
  }

  async function handleSubmit(event, type) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;

    const username = document.getElementById(type === 'login' ? 'loginUsername' : 'signupUsername').value;
    const password = document.getElementById(type === 'login' ? 'loginPassword' : 'signupPassword').value;
    const confirmPassword = type === 'signup'
      ? document.getElementById('signupConfirm').value
      : undefined;

    btn.innerHTML = `<i class="fas fa-spinner fa-pulse"></i> ${type === 'login' ? 'Logging in...' : 'Creating...'}`;
    btn.disabled = true;

    try {
      const body = { username, password };
      if (confirmPassword) body.confirm_password = confirmPassword;

      const res = await fetch(`/auth/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok) {
        const inputEl = document.getElementById(type === 'login' ? 'loginUsername' : 'signupUsername');
        showError(inputEl, data.detail || 'Something went wrong');
        return;
      }
      window.location.href = '/';
    } catch {
      const inputEl = document.getElementById(type === 'login' ? 'loginUsername' : 'signupUsername');
      showError(inputEl, 'Network error');
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  }

  loginForm.addEventListener('submit', (e) => handleSubmit(e, 'login'));
  signupForm.addEventListener('submit', (e) => handleSubmit(e, 'signup'));

  setActiveTab('login');
})();
