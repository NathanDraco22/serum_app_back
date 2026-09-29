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

## 3. Control de Acceso por Roles y Sucursales

- Cada usuario cuenta con un rol asignado (`admin`, `cashier`, `bioanalyst`, `doctor`, etc.).
- El campo `branches: list[str]` vincula al usuario a una o varias sedes físicas.
- Las operaciones financieras (apertura y cierre de caja) validan la vinculación activa del usuario con la sucursal de la caja correspondiente.
