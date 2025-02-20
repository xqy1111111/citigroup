import React from 'react';
import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const NavigateBar = () => {
    const navigate = useNavigate();

    const handleProjectClick = () => {
        navigate('/project');
    };

    const handleChatClick = () => {
        navigate('/chat');
    };

    return (
        <div style={{
            display: 'flex',
            gap: '20px',
            padding: '10px',
            backgroundColor: '#f5f5f5',
        }}>
            <Button
                variant="contained"
                onClick={handleProjectClick}
            >
                Project
            </Button>
            <Button
                variant="contained"
                onClick={handleChatClick}
            >
                Chat
            </Button>
        </div>
    );
};

export default NavigateBar;