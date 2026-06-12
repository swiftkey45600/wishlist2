import { Routes, Route, Navigate } from "react-router-dom"

import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"
import ProfilePage from "./pages/ProfilePage/ProfilePage";
import AuthPage from "./pages/AuthPage/AuthPage"

function App() {
  // function ProtectedRoute({ children }) {
  //   const token = localStorage.getItem("accessToken")
  //   return token ? children : <Navigate to="/auth" replace />
  // }

  return (
    

    <Routes>
      <Route 
        path="/auth" 
        element={<AuthPage />} 
      />

      <Route 
        path="/" 
        element={<HomePage />} 
      />

      <Route 
        path="/profile" 
        element={<ProfilePage />}
      />

      <Route 
        path="/events/:id" 
        element={<EventPage />}
      />
    </Routes>
  )
}

export default App
