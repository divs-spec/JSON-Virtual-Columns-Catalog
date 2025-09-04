const express = require('express');
const app = express();
app.use(express.json());


const pool = mysql.createPool({
host: 'db',
user: 'root',
password: 'root',
database: 'catalog'
});


const schemaMap = {
ram: { col: 'ram_gb', type: 'number' },
gpu: { col: 'gpu', type: 'string' },
screen_inches: { col: 'screen_in', type: 'number' },
battery_mAh: { col: 'battery_mah', type: 'number' }
};


function buildWhere(filters, params) {
const clauses = [];
for (const f of filters) {
const { field, op, value } = f;
const map = schemaMap[field];
if (map) {
const col = map.col;
if (op === '=' || op === '==') { clauses.push(`${col} = ?`); params.push(value); }
else if (op === '>=') { clauses.push(`${col} >= ?`); params.push(value); }
else if (op === '<=') { clauses.push(`${col} <= ?`); params.push(value); }
else if (op === 'IN') {
const placeholders = value.map(()=>'?').join(',');
clauses.push(`${col} IN (${placeholders})`);
params.push(...value);
} else {
clauses.push(`${col} ${op} ?`); params.push(value);
}
} else {
const path = `$.${field}`;
if (op === '=') { clauses.push(`JSON_UNQUOTE(JSON_EXTRACT(specs, '${path}')) = ?`); params.push(String(value)); }
else if (op === '>=') { clauses.push(`CAST(JSON_EXTRACT(specs, '${path}') AS DECIMAL) >= ?`); params.push(value); }
else { clauses.push(`JSON_EXTRACT(specs, '${path}') ${op} ?`); params.push(value); }
}
}
return clauses.length ? ('WHERE ' + clauses.join(' AND ')) : '';
}


app.post('/products/search', async (req, res) => {
const filters = req.body.filters || [];
const page = req.body.page || 1;
const pageSize = req.body.pageSize || 20;
const params = [];
const where = buildWhere(filters, params);
const offset = (page - 1) * pageSize;
const sql = `SELECT id, name, category, price, specs FROM products ${where} ORDER BY price LIMIT ? OFFSET ?`;
params.push(pageSize, offset);
try {
const [rows] = await pool.query(sql, params);
res.json({ rows });
} catch (err) {
console.error(err);
res.status(500).json({ error: err.message });
}
});


app.listen(3000, ()=>console.log('Listening on 3000'));
