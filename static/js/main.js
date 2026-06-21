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
    setTimeout(function(){alert("Thank you! Your inquiry has been received.\n\nContact us directly:\nEmail: mikelin88999@gmail.com
WhatsApp: +447599094629");btn.textContent="Send Inquiry";btn.disabled=false;e.target.reset();},1000);
  });}
});
