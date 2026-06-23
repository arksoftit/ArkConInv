## aci20260620001 – Duplicidad de importación de registros

### 📋 Descripción del Problema

Después de varias pruebas realizadas, se detectó que al momento de realizar la importación, si el usuario por alguna circunstancia  repite un rango de fecha ya procesado, a aplicación simplemente vuelva a realizar la importacion duplicando la información. Y como se ha de suponer ésto es totalmente inaceptable



### 🔍 Contexto

**Módulo/Componente**: Todos los módulos relacionados con la importación de los movimientos o transacciones de inventario Módulo importar\_transaccione.

- **Tablas Involucradas**: 

  - ark\_detalletranvtas	= 	SDetalleVenta

  - ark\_detalletrancomp	= 	SDetalleCompra

  - ark\_detalletraninv	= 	SDetalleInv

  - ark\_transacciones	= 	SOperacionInv

- **Escenario**: En éste momento es el comportamiento normal de la alicacion

### ✅ Comportamiento Esperado

No se debe permitir insertar movimientos duplicados, el usuario debe recibir un mensaje de notificación que ya ése periodo fue procesado 

### ❌ Comportamiento Actual

Duplica, triplica y no hay notificaciones al usuario

### 🛠️ Posibles Soluciones

1. Creación de un ID unico para cada tabla de SQLite, el cual se genera de un proceso de concatenación de los valores contenidos en FDI\_FECHAOPERACION, uo\_id, FDI\_TIPOOPERACION y FDI\_DOCUMENTO, ejemplo:  
Formato fecha	Numero Fecha	uo\_id	FDI\_TIPOOPERACION	FDI\_DOCUMENTO	IDUnico

2024-07-01	45292		1		11		0000225	452921110000225

2024-07-31	45322		1		11		0000226	453221110000226  
Creo que esto generará un idunico para cada transacción y lo insertaríamos en dtv\_idunico, dtc\_idunico, dti\_idunico y trn\_idunico, que se deben agregar a las tablas respectivas, así le delegaríamos esa tarea de validación a SQLite, tomamos el mensaje que nos devuelve y le notificamos al usuario, que ya existen transacciones importadas en el periodo seleccionado

### 📌 Prioridad

- [x] Crítico (bloquea funcionalidad)

- [ ] Alto (afecta funcionalidad principal)

- [ ] Medio (afecta funcionalidad secundaria)

- [ ] Bajo (mejora o detalle estético)

### 📎 Anexos

- \[Capturas de pantalla / Logs / Código relevante\]

### ✅ Estado

- [ ] Pendiente

- [x] En análisis

- [ ] En desarrollo

- [ ] Resuelto

- [ ] Descartado


