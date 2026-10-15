import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { RunDetail } from './pages/RunDetail'
import { Runs } from './pages/Runs'
import { Settings } from './pages/Settings'
import { Studio } from './pages/Studio'

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Studio />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/runs/:runId" element={<RunDetail />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}
