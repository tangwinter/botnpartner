const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.post('/chat', (req, res) => {
  const userMessage = req.body.message;
  res.json({ response: `You said: ${userMessage}` });
});

const port = process.env.PORT || 8005;
app.listen(port, () => {
  console.log(`Chatbot backend running on port ${port}`);
});