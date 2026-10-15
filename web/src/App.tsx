import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { PageScroll } from './components/PageScroll'
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
        <Route
          path="/runs"
          element={
            <PageScroll>
              <Runs />
            </PageScroll>
          }
        />
        <Route
          path="/runs/:runId"
          element={
            <PageScroll>
              <RunDetail />
            </PageScroll>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PageScroll>
              <Dashboard />
            </PageScroll>
          }
        />
        <Route
          path="/settings"
          element={
            <PageScroll>
              <Settings />
            </PageScroll>
          }
        />
      </Routes>
    </Layout>
  )
}
