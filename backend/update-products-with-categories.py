from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, RetailerCategory

def update_products_category_ids(db: Session):
    updated_count = 0

    # Tomamos todas las retailer_categories que ya tienen un category_id
    mappings = db.query(RetailerCategory).filter(RetailerCategory.category_id != None).all()
    mappings_count = len(mappings)
    current_mapping = 0

    for rc in mappings:
        print(f"🟢 Procesando retailer_category: {rc.name} - category_id: {rc.category_id}")
        print(f"Actualizando productos para retailer_category {current_mapping + 1} de {mappings_count}")
        # Para cada mapeo aplicamos la categoría al producto correspondiente
        products_to_update = db.query(Product).filter(
            Product.retailer_id == rc.retailer_id,
            Product.retail_category == rc.name
        ).all()

        for product in products_to_update:
            product.category_id = rc.category_id
            updated_count += 1

        db.commit()
        current_mapping += 1

    print(f"✅ Se actualizaron {updated_count} productos con su category_id correspondiente.")

if __name__ == "__main__":
    db = SessionLocal()
    update_products_category_ids(db)
