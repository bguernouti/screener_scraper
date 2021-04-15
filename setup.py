from models.tables import Base, engine

Base.metadata.create_all(bind=engine)

