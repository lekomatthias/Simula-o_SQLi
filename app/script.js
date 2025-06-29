
async function loadData() {
  const response = await fetch("/dados");
  const data = await response.json();

  const tbody = document.getElementById("dataTableBody");
  tbody.innerHTML = "";

  data.forEach((item) => {
    const row = document.createElement("tr");

    const cellId = document.createElement("td");
    cellId.textContent = item.id;

    const cellDado = document.createElement("td");
    cellDado.textContent = item.dado;

    row.appendChild(cellId);
    row.appendChild(cellDado);
    tbody.appendChild(row);
  });
}

document.getElementById("dataForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const dado = document.getElementById("dado").value;

  const response = await fetch("/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dado })
  });

  const result = await response.json();

  // Exibe a resposta JSON retornada do backend
  alert("Server Response:\n" + JSON.stringify(result, null, 2));

  document.getElementById("dado").value = "";
  await loadData();
});


window.onload = loadData;
