import { Routes, Route } from "react-router-dom"

import HomePage from "./pages/HomePage/HomePage"
import EventPage from "./pages/EventPage/EventPage"

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
    </Routes>
  )
}

export default App
