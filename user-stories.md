# User Stories

## 🧾 User Story 1  
**Como cliente, quiero consultar el estado de mi pedido ingresando el número de orden para saber cuándo llegará.**

### Acceptance Criteria:
- **Given** que el cliente tiene un número de orden válido,  
  **When** lo ingresa en el chatbot,  
  **Then** el chatbot debe mostrar el estado actual del pedido, la fecha estimada de entrega y el número de seguimiento si está disponible.

- **Given** que el número de orden es inválido o no existe,  
  **When** el cliente lo ingresa,  
  **Then** el chatbot debe informar que no se encontró el pedido y ofrecer asistencia adicional.

---

## 🔍 User Story 5  
**Como cliente, quiero buscar productos por nombre o categoría para encontrar lo que necesito rápidamente.**

### Acceptance Criteria:
- **Given** que el cliente escribe el nombre o categoría de un producto,  
  **When** el chatbot recibe la consulta,  
  **Then** debe mostrar una lista de productos relevantes con nombre, imagen, precio y disponibilidad.

- **Given** que no hay coincidencias con la búsqueda,  
  **When** el cliente realiza la consulta,  
  **Then** el chatbot debe sugerir categorías relacionadas o permitir refinar la búsqueda.

---

## 🛒 User Story 7  
**Como cliente, quiero agregar productos al carrito desde el chat para facilitar mi compra.**

### Acceptance Criteria:
- **Given** que el cliente selecciona un producto desde el chat,  
  **When** elige la opción “Agregar al carrito”,  
  **Then** el chatbot debe confirmar que el producto fue agregado correctamente y mostrar el total actualizado.

- **Given** que el producto está fuera de stock,  
  **When** el cliente intenta agregarlo,  
  **Then** el chatbot debe informar que no está disponible y ofrecer productos similares.

---

## 💳 User Story 10  
**Como cliente, quiero que el chatbot me guíe en el proceso de pago para completar mi compra sin errores.**

### Acceptance Criteria:
- **Given** que el cliente tiene productos en el carrito,  
  **When** solicita iniciar el pago,  
  **Then** el chatbot debe mostrar los métodos de pago disponibles y guiar paso a paso hasta la confirmación.

- **Given** que ocurre un error durante el pago,  
  **When** el cliente lo reporta o el sistema lo detecta,  
  **Then** el chatbot debe informar el problema y ofrecer alternativas o asistencia.
