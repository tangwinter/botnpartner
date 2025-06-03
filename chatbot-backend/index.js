const express = require('express');
const cors = require('cors');
const xlsx = require('xlsx');
const axios = require('axios');
const path = require('path');
const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../8003'))); // Serve static files from 8003 directory

// Deepseek config
const DEEPSEEK_API_KEY = 'BM7BodPC9CVF8G1J0PD97KCFvcO9Tfdo5NxFEgci6TPjGfkL3EbYJQQJ99BDACYeBjFXJ3w3AAAAACOGGHm2';
const DEEPSEEK_ENDPOINT = 'https://ds32.services.ai.azure.com/models';
const DEEPSEEK_MODEL = 'deepseek-v3';

// Load FAQ dataset
function loadFaqDataset() {
    try {
        const excelPath = path.join(__dirname, '(Bot4Pro) Simulated FAQ Dataset (with topic).xlsx');
        console.log('Loading Excel file from:', excelPath);
        const workbook = xlsx.readFile(excelPath);
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });
        // Remove header row if present
        if (typeof data[0][0] === 'string' && data[0][0].toLowerCase().includes('topic')) data.shift();
        return data.map(row => ({ topic: row[0], faq: row[1] }));
    } catch (error) {
        console.error('Error loading FAQ dataset:', error);
        throw error;
    }
}

const faqData = loadFaqDataset();

const WARNING_MESSAGE = "<br><br>Warning: The response above is given by our AI BD Manager powered by DeepSeek and there is no assurance that all information is accurate. If you need any legal advice, you should contact our lawyers.";

// System prompts
const TOPIC_IDENTIFICATION_PROMPT = (topics, question) => `
You are an experienced legal practitioner in Hong Kong. Given a list of legal topics and a question, you MUST select the top 3 most relevant topics that would help answer the question.

Available topics:
${topics.join('\n')}

Question: ${question}

List ONLY the top 3 most relevant topics in order of relevance, numbered 1-3. Do not include any other text or explanation.`;

const SYSTEM_PROMPT = `You are an experienced business development manager of a law firm but you are not a qualified lawyer. Your role is to provide helpful, professional guidance to clients and, very importantly to provide fee range for clients' reference.  Your job is to market your firm's service and drive business.\n\nKey guidelines:\n1. You should derive your response from the content of the FAQs.  You can expand the meaning of the FAQ naturally. \n2. Respond directly and conversationally, as if speaking from your own experience, but never mention about the existence of the FAQs.\n3. Provide practical examples and general guidance when appropriate\n4. Avoid giving specific legal advice nor solid suggestions on how the matter should be structure nor the detailed steps.  Use examples if you want to give suggestions, (e.g. depending on the client's circumstances, we may suggest [], but this would depend on your objective and our lawyer needs to have more details from you to provided with any recommendation that suits your need")\n5. Always try to explain how your lawyers can help the user and provide a fee range.  If you don't find a fee range for the exact kind of work asked by the client, you should read in the context of the relevant FAQ and provide the standard work and fee range provided in there.\n6. If you want to say something but consider that it may be inappropriate to say so given the guidance above, try to say what is already provided in the relevant FAQ.  Don't stop without finishing what you are saying.\n7. Always include an email address for the client to contact your firm if you are asking whether client would like you to connect him with your lawyers (e.g. "If you would like us to connect you with our specialist, please email us on: [email address]").\n8. Always add a + sign at the top end of the fee range (e.g. "HK$10,000 to HK$15,000+") to leave room for your lawyers to quote higher fees in a complicated case\n\nRemember: You are speaking as an experienced manager, not as an AI or documentation system. Your responses should reflect your expertise and experience in the field.`;

function formatResponse(responseText, selectedTopics) {
    let formatted = responseText.trim();
    formatted = formatted.replace(/\*\*/g, '<strong>').replace(/\*/g, '<em>');
    formatted = formatted.replace(/- /g, '<br>• ').replace(/• /g, '<br>• ');
    formatted = formatted.replace(/(\d+)\. /g, '<br>$1. ');
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = `<p>${formatted}</p>`;
    if (selectedTopics && selectedTopics.length > 0) {
        formatted += `<p>Selected Topics: ${selectedTopics.join(', ')}</p>`;
    }
    formatted += `<p>${WARNING_MESSAGE}</p>`;
    return formatted;
}

function extractTopTopics(responseText) {
    const lines = responseText.split('\n');
    const topics = [];
    for (const line of lines) {
        const match = line.match(/^\d+\.\s*(.+)$/);
        if (match) topics.push(match[1].trim());
    }
    return topics.slice(0, 3);
}

app.post('/chat', async (req, res) => {
    const userMessage = req.body.message;
    if (!userMessage) return res.json({ error: 'No message provided' });

    try {
        // 1. Get topics from FAQ
        const topics = faqData.map(row => row.topic);

        // 2. Ask Deepseek for top topics
        const topicPrompt = TOPIC_IDENTIFICATION_PROMPT(topics, userMessage);
        const topicResponse = await axios.post(
            DEEPSEEK_ENDPOINT,
            {
                model: DEEPSEEK_MODEL,
                messages: [
                    { role: 'system', content: topicPrompt },
                    { role: 'user', content: userMessage }
                ]
            },
            { headers: { 'api-key': DEEPSEEK_API_KEY, 'Content-Type': 'application/json' } }
        );
        const selectedTopics = extractTopTopics(topicResponse.data.choices[0].message.content);

        // 3. Ask Deepseek for the answer
        const response = await axios.post(
            DEEPSEEK_ENDPOINT,
            {
                model: DEEPSEEK_MODEL,
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    { role: 'user', content: userMessage }
                ]
            },
            { headers: { 'api-key': DEEPSEEK_API_KEY, 'Content-Type': 'application/json' } }
        );
        const formattedResponse = formatResponse(response.data.choices[0].message.content, selectedTopics);

        res.json({ response: formattedResponse });
    } catch (e) {
        console.error(e);
        res.json({ error: 'Unable to connect to chat service. Please try again later.' });
    }
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../8003/index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
    console.log(`Website is accessible at:`);
    console.log(`- http://localhost:${port}`);
    console.log(`- http://127.0.0.1:${port}`);
});