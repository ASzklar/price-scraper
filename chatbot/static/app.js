const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("question");

function agregarMensaje(texto, clase) {
  const div = document.createElement("div");
  div.className = `msg ${clase}`;
  div.textContent = texto;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

agregarMensaje(
  "Hola! Soy Veganito, tu asistente amigo para encontrar los mejores precios veganos. " +
  "Preguntame por ejemplo: 'dónde es más barata la Not Milk?' o 'qué producto de Vegetalex disminuyó más de precio en el último mes?'",
  "bot"
);

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const pregunta = input.value.trim();
  if (!pregunta) return;

  agregarMensaje(pregunta, "user");
  input.value = "";
  const boton = form.querySelector("button");
  boton.disabled = true;
  const pensando = agregarMensaje("Pensando...", "bot");

  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: pregunta }),
    });
    const datos = await resp.json();
    pensando.textContent = datos.answer;
  } catch (error) {
    pensando.textContent = "Uh, hubo un error de conexión. Probá de nuevo.";
  } finally {
    boton.disabled = false;
    input.focus();
  }
});
