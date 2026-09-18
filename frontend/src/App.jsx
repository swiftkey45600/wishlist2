import { Routes, Route, Navigate } from "react-router-dom"

import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"
import ProfilePage from "./pages/ProfilePage/ProfilePage";
import AuthPage from "./pages/AuthPage/AuthPage"
import PublicEventPage from "./pages/PublicEventPage/PublicEventPage"
import PresentsPage from "./pages/PresentsPage/PresentsPage"

function App() {
  function ProtectedRoute({ children }) {
    const token = localStorage.getItem("accessToken")
    return token ? children : <Navigate to="/auth" replace />
  }

  return (
    

    <Routes>
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
        element={<ProtectedRoute><PublicEventPage /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  )
}

export default App
