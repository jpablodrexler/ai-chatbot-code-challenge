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

**Endpoint REST:**  
`GET http://127.0.0.1:5000/orders/{order_id}`

**Ejemplo:**  
`GET http://127.0.0.1:5000/orders/1`

**Respuesta ejemplo:**  
```json
{
  "order_id": 1,
  "details": {
    "item": "Laptop",
    "quantity": 1,
    "status": "En tránsito",
    "estimated_delivery": "2024-08-05",
    "tracking_number": "ABC123456"
  }
}
```

---

## 🔍 User Story 2  
**Como cliente, quiero buscar productos por nombre o categoría para encontrar lo que necesito rápidamente.**

### Acceptance Criteria:
- **Given** que el cliente escribe el nombre o categoría de un producto,  
  **When** el chatbot recibe la consulta,  
  **Then** debe mostrar una lista de productos relevantes con nombre, imagen, precio y disponibilidad.

- **Given** que no hay coincidencias con la búsqueda,  
  **When** el cliente realiza la consulta,  
  **Then** el chatbot debe sugerir categorías relacionadas o permitir refinar la búsqueda.

**Endpoint REST:**  
`GET http://127.0.0.1:5000/products?search={nombre_o_categoria}`

**Ejemplo:**  
`GET http://127.0.0.1:5000/products?search=laptop`

**Respuesta ejemplo:**  
```json
[
  {
    "product_id": 101,
    "name": "Laptop",
    "image": "https://example.com/laptop.jpg",
    "price": 1200,
    "available": true
  }
]
```

---

## 🛒 User Story 3  
**Como cliente, quiero agregar productos al carrito desde el chat para facilitar mi compra.**

### Acceptance Criteria:
- **Given** que el cliente selecciona un producto desde el chat,  
  **When** elige la opción “Agregar al carrito”,  
  **Then** el chatbot debe confirmar que el producto fue agregado correctamente y mostrar el total actualizado.

- **Given** que el producto está fuera de stock,  
  **When** el cliente intenta agregarlo,  
  **Then** el chatbot debe informar que no está disponible y ofrecer productos similares.

**Endpoint REST:**  
`POST http://127.0.0.1:5000/cart/add`

**Ejemplo:**  
```json
{
  "product_id": 101,
  "quantity": 1
}
```

**Respuesta ejemplo:**  
```json
{
  "message": "Producto agregado al carrito",
  "cart_total": 1200
}
```

---

## 💳 User Story 4  
**Como cliente, quiero que el chatbot me guíe en el proceso de pago para completar mi compra sin errores.**

### Acceptance Criteria:
- **Given** que el cliente tiene productos en el carrito,  
  **When** solicita iniciar el pago,  
  **Then** el chatbot debe mostrar los métodos de pago disponibles y guiar paso a paso hasta la confirmación.

- **Given** que ocurre un error durante el pago,  
  **When** el cliente lo reporta o el sistema lo detecta,  
  **Then** el chatbot debe informar el problema y ofrecer alternativas o asistencia.

**Endpoint REST:**  
`POST http://127.0.0.1:5000/checkout`

**Ejemplo:**  
```json
{
  "cart_id": 55,
  "payment_method": "credit_card",
  "card_info": "**** **** **** 1234"
}
```

**Respuesta ejemplo:**  
```json
{
  "message": "Pago realizado con éxito",
  "order_id": 1,
  "status": "Confirmado"
}
```
