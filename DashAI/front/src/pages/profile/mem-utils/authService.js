import { MOCK_USERS } from "./mockInstance";

/**
 * Toy authentication service. Accounts live in localStorage (seeded from
 * MOCK_USERS), so sessions and new accounts survive a reload but only exist in
 * the current browser. This is the only module to replace when the backend
 * provides real authentication: keep the same async functions and call the
 * API instead.
 */

const USERS_KEY = "dashai-demo-users";
const SESSION_KEY = "dashai-demo-session";

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage unavailable (private mode, quota): the session lasts until reload
  }
}

function loadUsers() {
  return readStorage(USERS_KEY, MOCK_USERS);
}

function saveUsers(users) {
  writeStorage(USERS_KEY, users);
}

// The password never leaves this module
function toPublicUser(user) {
  const publicUser = { ...user };
  delete publicUser.password;
  return publicUser;
}

export async function getUsers() {
  return loadUsers().map(toPublicUser);
}

export async function getCurrentUser() {
  const userId = readStorage(SESSION_KEY, null);
  const user = loadUsers().find(
    (candidate) => candidate.id === userId && candidate.active,
  );
  return user ? toPublicUser(user) : null;
}

export async function login(email, password) {
  const user = loadUsers().find(
    (candidate) => candidate.email.toLowerCase() === email.toLowerCase(),
  );
  if (!user || user.password !== password) {
    throw new Error("Correo o contraseña incorrectos.");
  }
  if (!user.active) {
    throw new Error(
      "Esta cuenta está desactivada. Contacta a un administrador.",
    );
  }
  writeStorage(SESSION_KEY, user.id);
  return toPublicUser(user);
}

export async function logout() {
  writeStorage(SESSION_KEY, null);
}

export async function register({ name, nickname, email, password }) {
  const users = loadUsers();
  if (users.some((user) => user.email.toLowerCase() === email.toLowerCase())) {
    throw new Error("Ya existe una cuenta con ese correo.");
  }
  if (users.some((user) => user.nickname === nickname)) {
    throw new Error("Ese nickname ya está en uso.");
  }

  const user = {
    id: `USR-${Date.now()}`,
    email,
    password,
    legalName: name,
    socialName: name,
    nickname,
    bio: "",
    phone: "",
    github: "",
    linkedin: "",
    organization: "",
    position: "",
    globalRole: "Miembro",
    active: true,
  };
  saveUsers([...users, user]);
  return toPublicUser(user);
}

export async function updateUser(userId, changes) {
  const safeChanges = { ...changes };
  delete safeChanges.password;

  const users = loadUsers().map((user) =>
    user.id === userId ? { ...user, ...safeChanges } : user,
  );
  saveUsers(users);
  return users.map(toPublicUser);
}

export async function changePassword(userId, currentPassword, newPassword) {
  const users = loadUsers();
  const user = users.find((candidate) => candidate.id === userId);
  if (!user || user.password !== currentPassword) {
    throw new Error("La contraseña actual no es correcta.");
  }
  saveUsers(
    users.map((candidate) =>
      candidate.id === userId
        ? { ...candidate, password: newPassword }
        : candidate,
    ),
  );
}

/**
 * Drops every stored change (new accounts, edits, session) and goes back to
 * MOCK_USERS. Used by the debug tools of the login view.
 */
export async function resetDemoData() {
  writeStorage(USERS_KEY, null);
  writeStorage(SESSION_KEY, null);
}
