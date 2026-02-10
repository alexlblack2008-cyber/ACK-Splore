const express = require("express");
const path = require("path");
const dotenv = require("dotenv");
dotenv.config();

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const BASE_URL = process.env.BASE_URL || "http://localhost:4242";

// Simple demo reminder so you know it’s running
app.get("/", (req, res) => {
  res.send("ACK-Splore server is running.");
});

// IMPORTANT: Render uses process.env.PORT
const PORT = process.env.PORT || 4242;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));