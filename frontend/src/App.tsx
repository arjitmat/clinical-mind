import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { Landing } from './pages/Landing';
import { CaseBrowser } from './pages/CaseBrowser';
import { CaseInterface } from './pages/CaseInterface';
import { Dashboard } from './pages/Dashboard';
import { KnowledgeGraphPage } from './pages/KnowledgeGraph';
import { DemoLive } from './pages/DemoLive';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/cases" element={<CaseBrowser />} />
          <Route path="/case/:id" element={<CaseInterface />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
          <Route path="/demo" element={<DemoLive />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
