const express = require('express');
const app = express();

// Add basic logging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    next();
});

app.get('/', (req, res) => {
    console.log('Root endpoint hit');
    res.send('Test server is running!');
});

// Add a health check endpoint
app.get('/health', (req, res) => {
    console.log('Health check endpoint hit');
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        nodeVersion: process.version,
        environment: process.env.NODE_ENV || 'development'
    });
});

const port = process.env.PORT || 8006;
app.listen(port, () => {
    console.log(`Test server running on port ${port}`);
    console.log(`Node version: ${process.version}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
}); 