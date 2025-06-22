document.getElementById("dataForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const dado = document.getElementById("dado").value;

  await fetch("/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dado })
  });

  alert("Dados enviados!");
});
