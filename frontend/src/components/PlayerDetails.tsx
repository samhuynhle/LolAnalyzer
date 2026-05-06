import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const PlayerDetails: React.FC = () => {
    const { userId } = useParams<{ userId: string }>();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (userId) fetchDetails();
    }, [userId]);

    const fetchDetails = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`/api/players/${encodeURIComponent(userId!)}`);
            setData(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to load player details.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <p>Loading player data...</p>;
    if (error) return <p className="error">{error}</p>;
    if (!data) return <p>No data found.</p>;

    const { metadata, reports, matches } = data;
    const playerSlug = userId?.replace("#", "_").replace(" ", "_");

    return (
        <div className="player-details">
            <Link to="/" className="back-link">← Back to Dashboard</Link>
            <h1>{metadata.name}#{metadata.tag}</h1>
            <p>Region: {metadata.region?.toUpperCase()}</p>
            <p>First Seen: {metadata.first_seen}</p>
            <p>Last Analysis: {metadata.last_analysis}</p>

            <div className="history-grid">
                <section className="reports-history">
                    <h2>Analysis Reports</h2>
                    {Object.keys(reports).length === 0 ? (
                        <p>No reports generated.</p>
                    ) : (
                        <ul>
                            {Object.entries(reports).map(([id, r]: [string, any]) => (
                                <li key={id}>
                                    <Link to={`/report/${playerSlug}/${id}`}>
                                        {r.timestamp} - {r.matches_processed} matches
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                <section className="matches-history">
                    <h2>Match History (Local Cache)</h2>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Champion</th>
                                    <th>Role</th>
                                    <th>Result</th>
                                    <th>K/D/A</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.values(matches).map((m: any) => (
                                    <tr key={m.match_id}>
                                        <td>{m.timestamp}</td>
                                        <td>{m.champion}</td>
                                        <td>{m.role}</td>
                                        <td className={m.win ? 'win' : 'loss'}>{m.win ? 'WIN' : 'LOSS'}</td>
                                        <td>{m.kills}/{m.deaths}/{m.assists}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default PlayerDetails;
