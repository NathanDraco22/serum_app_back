---
type: doc
title: Reglas de Negocio — Autenticación, Tokens JWT y Roles
description: Flujo de inicio de sesión, estructura de tokens de sesión y refresh, verificación de estado de cuenta y control de acceso.
tags: [auth, jwt, security, users, roles, sessions]
timestamp: 2026-09-28T18:30:00Z
---

# 🔐 Autenticación, Tokens y Roles

## 1. Mecanismo de Tokens JWT (HS256)

La autenticación utiliza una arquitectura de doble token para asegurar sesiones persistentes sin comprometer la seguridad:

| Token | Vida Útil | Propósito | Header / Uso |
| :--- | :--- | :--- | :--- |
| **Session Token** | 8 horas | Autorización de peticiones HTTP a endpoints protegidos. | `Authorization: Bearer <sessionToken>` |
| **Refresh Token** | 30 días | Renovación periódica del session token sin pedir contraseña nuevamente. | Body en `POST /api/v1/auths/refresh-token` |

*Nota de formato*: Los claims de tiempo de JWT (`exp`, `iat`) utilizan **segundos Unix estándar** (RFC 7519), mientras que las marcas de tiempo en la base de datos MongoDB (`createdAt`, `updatedAt`) utilizan **milisegundos Unix**.

---

## 2. Endpoints del Módulo de Autenticación (`/api/v1/auths`)

1. **`POST /login`**:
   - Permite inicio de sesión flexible mediante `username`, `email` o `phone` junto con `password`.
   - Retorna el modelo del usuario (sin el campo `password`), el `token` de sesión y el `refreshToken`.
2. **`POST /refresh-token`**:
   - Valida la validez de la firma del `refreshToken` y confirma que el usuario aún exista en la base de datos y no esté borrado.
   - Retorna una nueva tupla de `token` y `refreshToken`.
3. **`POST /check-user`**:
   - Evalúa el estado del usuario asociado a un token de sesión activo.
   - Retorna:
     - `"active"`: Usuario habilitado y operativo.
     - `"unactive"`: Usuario deshabilitado por un administrador (`isActive = False`).
     - `"deleted"`: Usuario eliminado lógicamente (`isDeleted = True`).

---

## 3. Control de Acceso por Niveles Jerárquicos (`accessLevel`) y Roles

- Cada rol pertenece a una jerarquía de niveles del **1 al 5**:
  - **Nivel 5 (Admin)**: Acceso total al sistema, configuraciones globales, finanzas, infraestructura y administración de usuarios/roles.
  - **Nivel 4 (Supervisor)**: Autorizaciones especiales, auditoría y cierres de turno.
  - **Nivel 3 (Operador)**: Módulo POS de cobro, caja activa, registro de pacientes, cotizaciones y órdenes clínicas.
  - **Nivel 2 (Asistente)**: Recepción de pacientes y consultas operativas básicas.
  - **Nivel 1 (Consulta)**: Modo solo lectura para visualización clínica básica.
- El modelo de usuario incluye `accessLevel: int` desnormalizado, transmitido en el payload del JWT de sesión para verificaciones $O(1)$ sin queries a base de datos.
- El campo `branches: list[str]` vincula al usuario a una o varias sedes físicas.
- Las operaciones financieras (apertura y cierre de turnos de caja) validan la vinculación activa del usuario con la sucursal correspondiente.

---

## 4. Inicialización en Startup (Lifespan)

Durante el arranque de la aplicación (`app_lifespan.py` ➔ `services_initializer.py`), el servidor garantiza de forma idempotente (`$setOnInsert`):

1. **Sucursal Origen (`ORIGIN_BRANCH`)**:
   - `id`: `"ORIGIN_BRANCH"`
   - `name`: `"Origen"`
   - `address`: `"Sede Principal"`
   - `phone`: `"00000000"`
2. **Caja Registradora Inicial (`ORIGIN_CASH`)**:
   - `id`: `"ORIGIN_CASH"`
   - `name`: `"Caja Principal"`
3. **Roles por Defecto (`Roles`)**:
   - `role_admin`: `"Admin"` con `accessLevel: 5`.
   - `role_operator`: `"Operador"` con `accessLevel: 3`.
4. **Usuario Administrador Root (`Serum`)**:
   - `id`: `"root"`
   - `username`: `"Serum"`
   - `password`: `"SerumRoot"` (almacenada con hash Argon2)
   - `name`: `"Administrador Serum"`
   - `role`: `"Admin"`
   - `accessLevel`: `5`
   - `branches`: `["ORIGIN_BRANCH"]`
   - `isActive`: `True`
