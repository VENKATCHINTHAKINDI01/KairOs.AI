import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import LaunchRoom from './pages/LaunchRoom'
import Dashboard  from './pages/Dashboard'
import Reports    from './pages/Reports'

export default function App() {
  return (
    <Routes>
      <Route path="/"          element={<LaunchRoom />} />
      <Route path="/warroom"   element={<LaunchRoom />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/reports"   element={<Reports />} />
      <Route path="*"          element={<Navigate to="/" replace />} />
    </Routes>
  )
}