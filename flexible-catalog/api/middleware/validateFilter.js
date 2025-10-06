module.exports = function validateFilter(req, res, next) {
  const { filters } = req.body;
  
  if (filters && !Array.isArray(filters)) {
    return res.status(400).json({ error: 'Filters must be an array' });
  }
  
  if (filters) {
    for (const filter of filters) {
      if (!filter.field || !filter.op) {
        return res.status(400).json({ 
          error: 'Each filter must have field and op' 
        });
      }
      
      const validOps = ['=', '!=', '>', '>=', '<', '<=', 'like', 'in'];
      if (!validOps.includes(filter.op)) {
        return res.status(400).json({ 
          error: `Invalid operator: ${filter.op}` 
        });
      }
      
      if (filter.value === undefined || filter.value === null) {
        return res.status(400).json({ 
          error: 'Filter value is required' 
        });
      }
    }
  }
  
  next();
};
