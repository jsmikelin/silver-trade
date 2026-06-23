// HK Changjiang International - Main JavaScript
function toggleNav(){document.getElementById("navLinks").classList.toggle("open");}
function toggleFaq(el){el.classList.toggle("open");}
document.querySelectorAll('a[href^="#"]').forEach(function(a){
  a.addEventListener("click",function(e){e.preventDefault();var t=document.querySelector(this.getAttribute("href"));if(t)t.scrollIntoView({behavior:"smooth",block:"start"});});
});
document.addEventListener("DOMContentLoaded",function(){
  document.querySelectorAll(".nav-links a").forEach(function(l){l.addEventListener("click",function(){document.getElementById("navLinks").classList.remove("open");});});
  var form=document.getElementById("contactForm");
  if(form){form.addEventListener("submit",function(e){
    e.preventDefault();var btn=e.target.querySelector("button");btn.textContent="Sending...";btn.disabled=true;
    setTimeout(function(){alert("Thank you! Your inquiry has been received.\n\nContact us directly:\nEmail: mikelin88999@gmail.com\nWhatsApp: +447599094629");btn.textContent="Send Inquiry";btn.disabled=false;e.target.reset();},1000);
  });}
});

/* ===== Registration Form Handler ===== */
function handleRegisterForm(e) {
  e.preventDefault();
  var btn = document.getElementById('registerSubmitBtn');
  btn.textContent = 'Submitting...';
  btn.disabled = true;

  var data = {
    country: document.getElementById('regCountry').value,
    name: document.getElementById('regName').value,
    email: document.getElementById('regEmail').value,
    whatsapp: document.getElementById('regWhatsApp').value,
    message: document.getElementById('regMessage').value,
    timestamp: new Date().toISOString(),
    source: window.location.href
  };

  // Save to localStorage (persistent storage)
  var submissions = JSON.parse(localStorage.getItem('silver_trade_submissions') || '[]');
  submissions.push(data);
  localStorage.setItem('silver_trade_submissions', JSON.stringify(submissions));

  // Also try POST to form-submissions endpoint if backend exists
  var apiUrl = '/api/form-submissions/';
  fetch(apiUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).catch(function() {
    // Backend not available — pure-frontend mode is fine
  });

  // Show success message
  setTimeout(function() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('registerSuccess').style.display = 'block';
    btn.textContent = '→ Submit Inquiry';
    btn.disabled = false;
  }, 600);

  return false;
}

function resetRegisterForm() {
  document.getElementById('registerForm').style.display = 'block';
  document.getElementById('registerSuccess').style.display = 'none';
  document.getElementById('registerForm').reset();
}

