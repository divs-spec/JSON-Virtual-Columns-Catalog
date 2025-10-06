const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
const morgan = require('morgan');
const compression = require('compression');
const helmet = require('helmet');
const { body, validationResult } = require('express-validator');
const validateFilter = require('./middleware/validateFilter');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());
app.use(morgan('combined'));

// Database connection pool
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 3306,
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASS || 'root',
  database: process.env.DB_NAME || 'catalog',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date() });
});

// Get all products with pagination
app.get('/products', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const offset = (page - 1) * limit;
    
    const [rows] = await pool.execute(
      'SELECT * FROM products LIMIT ? OFFSET ?',
      [limit, offset]
    );
    
    const [countResult] = await pool.execute('SELECT COUNT(*) as total FROM products');
    
    res.json({
      data: rows,
      pagination: {
        page,
        limit,
        total: countResult[0].total,
        pages: Math.ceil(countResult[0].total / limit)
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Database error' });
  }
});

// Search products with filters
app.post('/products/search', validateFilter, async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const { filters = [], sort, page = 1, pageSize = 20 } = req.body;
    const limit = Math.min(pageSize, 100);
    const offset = (page - 1) * limit;
    
    // Build WHERE clause
    let whereConditions = [];
    let params = [];
    
    filters.forEach(filter => {
      const { field, op, value } = filter;
      
      // Map fields to actual columns (generated or JSON paths)
      const columnMap = {
        'ram': 'ram_gb',
        'storage': 'storage_gb',
        'gpu': 'gpu',
        'screen_size': 'screen_size',
        'battery': 'battery_mah',
        'cpu': 'cpu',
        'brand': 'brand',
        'price': 'price',
        'category': 'category'
      };
      
      const column = columnMap[field] || field;
      
      switch(op) {
        case '=':
          whereConditions.push(`${column} = ?`);
          params.push(value);
          break;
        case '!=':
          whereConditions.push(`${column} != ?`);
          params.push(value);
          break;
        case '>':
          whereConditions.push(`${column} > ?`);
          params.push(value);
          break;
        case '>=':
          whereConditions.push(`${column} >= ?`);
          params.push(value);
          break;
        case '<':
          whereConditions.push(`${column} < ?`);
          params.push(value);
          break;
        case '<=':
          whereConditions.push(`${column} <= ?`);
          params.push(value);
          break;
        case 'like':
          whereConditions.push(`${column} LIKE ?`);
          params.push(`%${value}%`);
          break;
        case 'in':
          if (Array.isArray(value)) {
            whereConditions.push(`${column} IN (${value.map(() => '?').join(',')})`);
            params.push(...value);
          }
          break;
      }
    });
    
    let query = 'SELECT * FROM products';
    if (whereConditions.length > 0) {
      query += ' WHERE ' + whereConditions.join(' AND ');
    }
    
    // Add sorting
    if (sort) {
      const { field, order = 'asc' } = sort;
      const sortOrder = order.toLowerCase() === 'desc' ? 'DESC' : 'ASC';
      query += ` ORDER BY ${field} ${sortOrder}`;
    }
    
    // Add pagination
    query += ' LIMIT ? OFFSET ?';
    params.push(limit, offset);
    
    const [rows] = await pool.execute(query, params);
    
    // Get total count
    let countQuery = 'SELECT COUNT(*) as total FROM products';
    if (whereConditions.length > 0) {
      countQuery += ' WHERE ' + whereConditions.join(' AND ');
    }
    const [countResult] = await pool.execute(countQuery, params.slice(0, -2));
    
    res.json({
      data: rows,
      pagination: {
        page,
        pageSize: limit,
        total: countResult[0].total,
        pages: Math.ceil(countResult[0].total / limit)
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Database error' });
  }
});

// Get product by ID
app.get('/products/:id', async (req, res) => {
  try {
    const [rows] = await pool.execute(
      'SELECT * FROM products WHERE id = ?',
      [req.params.id]
    );
    
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json(rows[0]);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Database error' });
  }
});

// Get analytics
app.get('/analytics/summary', async (req, res) => {
  try {
    const [rows] = await pool.execute('SELECT * FROM product_summary');
    res.json(rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Database error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 API Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
