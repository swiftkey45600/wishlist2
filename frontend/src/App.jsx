import { Routes, Route } from "react-router-dom"

import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"
import ProfilePage from "./pages/ProfilePage/ProfilePage";
import AuthPage from "./pages/AuthPage/AuthPage"

function App() {
  return (
    <Routes>
      <Route 
        path="/"
        element={<HomePage />}
      />

      <Route 
        path="/events/:id"
        element={<EventPage />}
      />

      <Route 
        path="/profile"
        element={<ProfilePage />}
      />

      <Route
        path="/auth"
        element={<AuthPage />}
      />
    </Routes>
  )
}

export default App
