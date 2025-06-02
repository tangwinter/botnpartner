const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Test server is running!');
});

const port = process.env.PORT || 8005;
app.listen(port, () => {
    console.log(`Test server running on port ${port}`);
}); 