import { Routes, Route, Navigate } from "react-router-dom"

import { YandexCallback } from "./components/YandexAuth/YandexAuth"
import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"
import ProfilePage from "./pages/ProfilePage/ProfilePage";
import AuthPage from "./pages/AuthPage/AuthPage"
import PublicEventPage from "./pages/PublicEventPage/PublicEventPage"
import PasswordRecoveryPage from "./components/AccountEmail/PasswordRecoveryPage"
import PresentsPage from "./pages/PresentsPage/PresentsPage"
import SharedWishesPage from "./pages/SharedWishesPage/SharedWishesPage"

function ProtectedRoute({ children }) {
    const token = localStorage.getItem("accessToken")
    return token ? children : <Navigate to="/auth" replace />
}

function App() {
  return (
    

    <Routes>
      <Route path="/wishes/shared/:token" element={<SharedWishesPage />} />
      <Route path="/auth/yandex" element={<YandexCallback />} />
      <Route path="/forgot-password" element={<PasswordRecoveryPage />} />
      <Route path="/reset-password" element={<PasswordRecoveryPage reset />} />
      <Route 
        path="/auth" 
        element={<AuthPage />} 
      />

      <Route 
        path="/" 
        element={<ProtectedRoute><HomePage /></ProtectedRoute>} 
      />

      <Route 
        path="/profile" 
        element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
      />

      <Route
        path="/presents"
        element={<ProtectedRoute><PresentsPage /></ProtectedRoute>}
      />

      <Route 
        path="/events/:id" 
        element={<ProtectedRoute><EventPage /></ProtectedRoute>}
      />

      <Route 
        path="/share/:token"
        element={<PublicEventPage />} />

      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  )
}

export default App
