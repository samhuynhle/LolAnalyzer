import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
    const [players, setPlayers] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        tag: '',
        region: '',
        count: 52
    });
    
    const navigate = useNavigate();

    useEffect(() => {
        fetchPlayers();
    }, []);

    const fetchPlayers = async () => {
        try {
            const res = await axios.get('/api/players');
            setPlayers(res.data);
        } catch (err) {
            console.error("Error fetching players", err);
        }
    };

    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await axios.post('/api/analyze', formData);
            // After successful analysis, navigate to player details
            const userId = `${formData.name}#${formData.tag}`.toLowerCase();
            navigate(`/player/${encodeURIComponent(userId)}`);
        } catch (err: any) {
            setError(err.response?.data?.detail || "An error occurred during analysis.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard">
            <h1>LolAnalyzer</h1>
            
            <section className="analysis-form">
                <h2>New Analysis</h2>
                <form onSubmit={handleAnalyze}>
                    <div className="form-group">
                        <label>Riot Name</label>
                        <input 
                            type="text" 
                            required 
                            value={formData.name} 
                            onChange={e => setFormData({...formData, name: e.target.value})}
                            placeholder="e.g. Spear Shot"
                        />
                    </div>
                    <div className="form-group">
                        <label>Tag</label>
                        <input 
                            type="text" 
                            required 
                            value={formData.tag} 
                            onChange={e => setFormData({...formData, tag: e.target.value})}
                            placeholder="e.g. 1111"
                        />
                    </div>
                    <div className="form-group">
                        <label>Region (Optional)</label>
                        <input 
                            type="text" 
                            value={formData.region} 
                            onChange={e => setFormData({...formData, region: e.target.value})}
                            placeholder="e.g. euw1, na1"
                        />
                    </div>
                    <div className="form-group">
                        <label>Match Count</label>
                        <input 
                            type="number" 
                            value={formData.count} 
                            onChange={e => setFormData({...formData, count: parseInt(e.target.value)})}
                        />
                    </div>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Analyzing...' : 'Run Analysis'}
                    </button>
                </form>
                {error && <p className="error">{error}</p>}
                {loading && <p className="status">Analyzing matches... this may take a moment due to rate limits.</p>}
            </section>

            <section className="player-list">
                <h2>Analyzed Players</h2>
                {players.length === 0 ? (
                    <p>No players analyzed yet.</p>
                ) : (
                    <ul>
                        {players.map(p => (
                            <li key={p}>
                                <Link to={`/player/${encodeURIComponent(p)}`}>{p}</Link>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </div>
    );
};

export default Dashboard;
