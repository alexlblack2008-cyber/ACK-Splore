const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 4243;

app.use(express.static(path.join(__dirname, 'public')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Beer Die Rankings running on port ${PORT}`);
});
