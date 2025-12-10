const spinBtn = document.getElementById("spinBtn");
const resultDiv = document.getElementById("result");

// Replace with your rewards
const items = ["+1 Energy"];

spinBtn.addEventListener("click", () => {
  const selectedIndex = Math.floor(Math.random() * items.length);
  const reward = items[selectedIndex];
  resultDiv.textContent = `🎉 You got: ${reward}`;

  // Send reward to backend
  fetch("https://your-backend-url.onrender.com/spin", {  // <-- Render backend URL
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user: "Alice", reward })
  })
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
});