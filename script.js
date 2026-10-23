/**
 * AI Recruitment System - Shared Utilities & Auth Management
 */

const API_BASE = "http://127.0.0.1:8000";

function getCurrentUser() {
    try {
        const stored = localStorage.getItem("ai_recruit_user");
        return stored ? JSON.parse(stored) : null;
    } catch (e) {
        return null;
    }
}

function setCurrentUser(user) {
    localStorage.setItem("ai_recruit_user", JSON.stringify(user));
}

function logout() {
    localStorage.removeItem("ai_recruit_user");
    window.location.href = "login.html";
}

function requireAuth(allowedRole = null) {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = "login.html";
        return null;
    }
    if (allowedRole && user.role !== allowedRole && user.role !== "admin") {
        if (user.role === "candidate") {
            window.location.href = "candidate-dashboard.html";
        } else if (user.role === "hr") {
            window.location.href = "hr-dashboard.html";
        }
        return null;
    }
    return user;
}
