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

  function handleSubmit(event, type) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;

    if (type === 'signup') {
      const pass = document.getElementById('signupPassword').value;
      const confirm = document.getElementById('signupConfirm').value;
      if (pass !== confirm) {
        const confirmInput = document.getElementById('signupConfirm');
        confirmInput.style.borderColor = '#BF616A';
        confirmInput.style.background = '#3B2E38';
        setTimeout(() => {
          confirmInput.style.borderColor = '#434C5E';
          confirmInput.style.background = '#3B4252';
        }, 600);
        confirmInput.placeholder = '❌ passwords mismatch';
        setTimeout(() => confirmInput.placeholder = 'Confirm password', 1200);
        return;
      }
    }

    btn.innerHTML = `<i class="fas fa-spinner fa-pulse"></i> ${type === 'login' ? 'Logging in...' : 'Creating...'}`;
    btn.disabled = true;

    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }, 600);
  }

  loginForm.addEventListener('submit', (e) => handleSubmit(e, 'login'));
  signupForm.addEventListener('submit', (e) => handleSubmit(e, 'signup'));

  setActiveTab('login');
})();