import express from "express";
import mysql from "mysql2/promise";
import morgan from "morgan";
import dotenv from "dotenv";
import { validateFilter } from "./middleware/validateFilter.js";

dotenv.config();

const app = express();
app.use(express.json());
app.use(morgan("dev"));

// DB connection pool
const pool = mysql.createPool({
  host: process.env.DB_HOST || "db",
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASS || "root",
  database: process.env.DB_NAME || "catalog",
  waitForConnections: true,
  connectionLimit: 10,
});

// Healthcheck endpoint
app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// Product search
app.post("/products/search", validateFilter, async (req, res) => {
  try {
    const { filters = [], page = 1, pageSize = 20 } = req.body;
    const offset = (page - 1) * pageSize;

    // Map filterable fields to DB columns
    const fieldMap = {
      ram: "ram_gb",
      gpu: "gpu",
      screen_inches: "screen_in",
      battery: "battery_mah",
      price: "price",
    };

    let conditions = [];
    let values = [];

    for (let f of filters) {
      if (fieldMap[f.field]) {
        conditions.push(`${fieldMap[f.field]} ${f.op} ?`);
        values.push(f.value);
      } else {
        // fallback to JSON_EXTRACT for unindexed fields
        conditions.push(`JSON_UNQUOTE(JSON_EXTRACT(specs, '$.${f.field}')) ${f.op} ?`);
        values.push(f.value);
      }
    }

    const whereClause = conditions.length ? "WHERE " + conditions.join(" AND ") : "";
    const sql = `SELECT * FROM products ${whereClause} LIMIT ? OFFSET ?`;

    console.time("query");
    const [rows] = await pool.execute(sql, [...values, pageSize, offset]);
    console.timeEnd("query");

    res.json({ rows });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.listen(process.env.PORT || 3000, () => {
  console.log(`API running on port ${process.env.PORT || 3000}`);
});
