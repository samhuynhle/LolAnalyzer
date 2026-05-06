import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const ReportViewer: React.FC = () => {
    const { playerSlug, reportId } = useParams<{ playerSlug: string, reportId: string }>();
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (playerSlug && reportId) fetchReport();
    }, [playerSlug, reportId]);

    const fetchReport = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`/api/reports/${playerSlug}/${reportId}`);
            setContent(res.data.content);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to load report.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="report-viewer">
            <Link to={-1 as any} className="back-link">← Back</Link>
            <h1>Analysis Report</h1>
            {loading && <p>Loading report...</p>}
            {error && <p className="error">{error}</p>}
            {!loading && !error && (
                <pre className="report-content">
                    {content}
                </pre>
            )}
        </div>
    );
};

export default ReportViewer;
