import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { NewLanding } from './pages/NewLanding';
import SimulationInterface from './pages/SimulationInterface';
import { ReasoningChain } from './pages/ReasoningChain';
import { AdversarialCase } from './pages/AdversarialCase';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<NewLanding />} />
          <Route path="/simulation" element={<SimulationInterface />} />
          <Route path="/reasoning-chain" element={<ReasoningChain />} />
          <Route path="/adversarial" element={<AdversarialCase />} />
          {/* Additional routes will be added as features are built */}
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
