UPDATE products
SET category_id = rc.category_id
FROM retailer_categories rc
WHERE products.retailer_id = rc.retailer_id
  AND products.category = rc.name
  AND rc.category_id IS NOT NULL;
