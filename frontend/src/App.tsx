import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import PlayerDetails from './components/PlayerDetails';
import ReportViewer from './components/ReportViewer';
import './App.css';

function App() {
  return (
    <Router>
      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/player/:userId" element={<PlayerDetails />} />
          <Route path="/report/:playerSlug/:reportId" element={<ReportViewer />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
