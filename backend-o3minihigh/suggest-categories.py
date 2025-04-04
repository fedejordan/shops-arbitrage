from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RetailerCategory, Category

SIMILARITY_THRESHOLD = 70  # podés aflojar o endurecer esto

def interactive_suggestions(db: Session):
    retailer_cats = db.query(RetailerCategory).filter(RetailerCategory.category_id == None).all()
    categories = db.query(Category).all()
    print(f"🔍 Encontré {len(retailer_cats)} categorías de retailer sin mapeo.")

    for rc in retailer_cats:
        best_match = None
        best_score = 0

        for cat in categories:
            score = fuzz.partial_ratio(rc.name.lower(), cat.name.lower())
            if score > best_score:
                best_score = score
                best_match = cat

        if best_match and best_score >= SIMILARITY_THRESHOLD:
            print(f"\n❓ ¿Querés mapear '{rc.name}' → '{best_match.name}'? ({best_score}%)")
            resp = input("[y] sí, [n] no, [s] salir: ").strip().lower()

            if resp == "y":
                rc.category_id = best_match.id
                db.commit()
                print("✅ Mapeo guardado.")
            elif resp == "s":
                print("🛑 Saliendo del asistente.")
                break
            else:
                print("⏭️ Omitido.")

if __name__ == "__main__":
    db = SessionLocal()
    interactive_suggestions(db)
