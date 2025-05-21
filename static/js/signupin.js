// This file handles the toggling of the login and register forms in the signup/login page
const container = document.querySelector(".container");
const register = document.querySelector(".register-btn");
const login = document.querySelector(".login-btn");

register.addEventListener("click", () => {
  container.classList.add("active");
});

login.addEventListener("click", () => {
  container.classList.remove("active");
});
