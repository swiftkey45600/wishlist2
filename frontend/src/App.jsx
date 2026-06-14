import { Routes, Route, Navigate } from "react-router-dom"

import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"
import ProfilePage from "./pages/ProfilePage/ProfilePage";
import AuthPage from "./pages/AuthPage/AuthPage"
import PublicEventPage from "./pages/PublicEventPage/PublicEventPage"

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
        path="/events/:id" 
        element={<ProtectedRoute><EventPage /></ProtectedRoute>}
      />

      <Route 
        path="/share/:token"
        element={<PublicEventPage />} />
    </Routes>
  )
}

export default App
