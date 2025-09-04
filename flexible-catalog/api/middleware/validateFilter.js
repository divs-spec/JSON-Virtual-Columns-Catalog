import Ajv from "ajv";
const ajv = new Ajv();


const filterSchema = {
type: "object",
properties: {
field: { type: "string" },
op: { type: "string" },
value: {}
},
required: ["field", "op", "value"]
};


const validate = ajv.compile(filterSchema);


export function validateFilter(req, res, next) {
for (let f of req.body.filters || []) {
if (!validate(f)) return res.status(400).json({ error: "Invalid filter" });
}
next();
}
